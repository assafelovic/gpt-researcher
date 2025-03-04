from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Awaitable

from fastapi import UploadFile
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket as ServerWebSocket
from gpt_researcher.actions import stream_output
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.config import Config
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.utils.enum import ReportType, Tone
from werkzeug.utils import secure_filename

if TYPE_CHECKING:
    from backend.server.websocket_manager import WebSocketManager

logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger(__name__)


class HTTPStreamAdapter:
    """Adapter to make HTTP streaming look like a WebSocket for WebSocketManager"""

    def __init__(
        self,
        message_queue: asyncio.Queue[str],
    ):
        self.message_queue: asyncio.Queue[str] = message_queue
        self.client_state: dict[str, Any] = {"ready": True}
        self._closed: bool = False

    async def send_text(
        self,
        message: str,
    ) -> None:
        await self.message_queue.put(message)

    async def send_json(
        self,
        data: dict[str, Any],
    ) -> None:
        await self.message_queue.put(json.dumps(data, indent=2))

    # Required WebSocket compatibility methods
    async def accept(self) -> None:
        """Simulated WebSocket accept"""
        self._closed = False

    async def close(self) -> None:
        """Simulated WebSocket close"""
        self._closed = True

    @property
    def closed(self) -> bool:
        """Simulated WebSocket closed property"""
        return self._closed

    async def receive_text(self) -> str:
        """Simulated WebSocket receive text"""
        return ""

    async def receive_json(self) -> dict[str, Any]:
        """Simulated WebSocket receive JSON"""
        return {}


class CustomLogsHandler:
    """Custom handler to capture streaming logs from the research process."""

    def __init__(
        self,
        websocket: ServerWebSocket | HTTPStreamAdapter | None = None,
        task: str | None = None,
    ):
        self.websocket: ServerWebSocket | HTTPStreamAdapter | None = websocket
        self.logs: list[dict[str, Any]] = []
        self.timestamp: str = datetime.now().isoformat()

        # Initialize log file with metadata
        sanitized_filename: str = sanitize_filename(f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{task}")
        self.log_file: Path = Path(os.path.expandvars(os.path.join("outputs", f"{sanitized_filename}.json"))).absolute()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.write_text(
            json.dumps(
                {
                    "timestamp": self.timestamp,
                    "events": [],
                    "content": {
                        "query": "",
                        "sources": [],
                        "context": [],
                        "report": "",
                        "costs": 0.0,
                    },
                },
                indent=2,
            )
        )

    async def send_json(
        self,
        data: dict[str, Any],
    ) -> None:
        """Store log data and send to websocket."""
        if self.websocket is not None:
            await self.websocket.send_json(data)

        log_data: dict[str, Any] = json.loads(self.log_file.read_text().strip())

        if str(data.get("type")).casefold() == "logs":
            events_list: list[dict[str, Any]] = log_data["events"]
            events_list.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "event",
                    "data": data,
                }
            )
        else:
            content_dict: dict[str, Any] = log_data["content"]
            content_dict.update(data)

        self.log_file.write_text(json.dumps(log_data, indent=2))
        logger.debug(f"Log entry written to: '{self.log_file}'")


class Researcher:
    def __init__(
        self,
        query: str,
        report_type: str | ReportType = ReportType.ResearchReport,
        websocket: CustomLogsHandler | ServerWebSocket | None = None,
    ):
        self.query: str = str(query or "").strip()
        self.report_type: ReportType = (
            ReportType.__members__[report_type.lower().title()]
            if isinstance(report_type, str)
            else report_type
        )
        self.research_id: str = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(self.query)}"
        self.logs_handler: CustomLogsHandler | None = None
        if isinstance(websocket, ServerWebSocket):  # fastapi
            self.logs_handler = CustomLogsHandler(websocket=websocket, task=self.query)
        elif isinstance(websocket, CustomLogsHandler):  # flask-socketio
            self.logs_handler = websocket
        else:
            raise ValueError("Invalid websocket type")

        self.researcher: GPTResearcher = GPTResearcher(
            query=self.query,
            config=Config(REPORT_TYPE=self.report_type),
            websocket=self.logs_handler,
            report_type=self.report_type,
        )

    async def research(self) -> dict[str, Any]:
        """Conduct research and return paths to generated files."""
        await self.researcher.conduct_research()
        report: str = await self.researcher.write_report()

        sanitized_filename: str = sanitize_filename(
            f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.query}"
        )
        file_paths: dict[str, Path] = await generate_report_files(report, sanitized_filename)

        if self.logs_handler is not None and self.logs_handler.log_file.exists() and self.logs_handler.log_file.is_file():
            json_relative_path: Path = self.logs_handler.log_file.relative_to(Path.cwd().absolute())
        else:
            json_relative_path: Path = Path("")

        return {
            "output": {
                **file_paths,  # Include PDF, DOCX, and MD paths
                "json": json_relative_path,
            }
        }


def sanitize_filename(filename: str) -> str:
    prefix, timestamp, *task_parts = filename.split("_")
    task: str = "_".join(task_parts)

    # Calculate max length for task portion
    # 255 - len("outputs/") - len("task_") - len(timestamp) - len("_.json") - safety_margin
    max_task_length = 255 - 8 - 5 - 10 - 6 - 10  # ~216 chars for task

    # Truncate task if needed
    truncated_task: str = task[:max_task_length] if len(task) > max_task_length else task

    # Reassemble and clean the filename
    sanitized: str = f"{prefix}_{timestamp}_{truncated_task}"
    return re.sub(r"[^\w\s-]", "", sanitized).strip()


async def handle_start_command(
    websocket: ServerWebSocket,
    data: str,
    manager: WebSocketManager,
):
    json_data: dict[str, Any] = json.loads(data[6:])
    (
        task,
        report_type,
        source_urls,
        document_urls,
        tone,
        headers,
        report_source,
        query_domains,
    ) = extract_command_data(json_data)

    if not str(task or "").strip() or not str(report_type or "").strip():
        logger.error("Error: Missing task or report_type")
        return

    # Create logs handler with websocket and task
    logs_handler = CustomLogsHandler(
        websocket=websocket,
        task=task,
    )
    # Initialize log content with query
    await logs_handler.send_json(
        {
            "query": task,
            "sources": [],
            "context": [],
            "report": "",
        }
    )

    report: str = await manager.start_streaming(
        task=str(task or "").strip(),
        report_type=str(report_type or "").strip(),
        report_source=str(report_source or "").strip(),
        source_urls=source_urls or [],
        document_urls=document_urls or [],
        tone=tone or Tone.Objective,
        websocket=websocket,
        headers=headers,
        query_domains=query_domains or [],
    )
    sanitized_filename: str = sanitize_filename(f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(task or '').strip()}")
    # Generate the files
    file_paths: dict[str, Path] = await generate_report_files(
        str(report or "").strip(),
        str(sanitized_filename or "").strip(),
    )
    file_paths["json"] = logs_handler.log_file.relative_to(Path.cwd().absolute())
    await send_file_paths(websocket=websocket, file_paths=file_paths)


async def handle_human_feedback(data: str) -> None:
    feedback_data: dict[str, Any] = json.loads(data[14:])  # Remove "human_feedback" prefix
    logger.debug(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state


async def handle_chat(
    websocket: ServerWebSocket,
    data: str,
    manager: WebSocketManager,
) -> str | None:
    json_data: dict[str, Any] = json.loads(data[4:])
    logger.debug(f"Received chat message: {json_data['message']}")
    return await manager.chat(str(json_data["message"] or "").strip(), websocket)


async def generate_report_files(report: str, base_filename: str) -> dict[str, Path]:
    """
    Generate report files in different formats.
    
    Args:
        report: The report content in markdown format
        base_filename: The base filename to use for the reports
        
    Returns:
        A dictionary mapping format names to file paths
    """
    try:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        base_path: Path = reports_dir / base_filename
        md_path: Path = base_path.with_suffix(".md")
        md_path.write_text(report)
        result: dict[str, Path] = {"md": md_path}
        try:
            from backend.utils import write_md_to_pdf
            await write_md_to_pdf(report)
            pdf_path: Path = base_path.with_suffix(".pdf")
            result["pdf"] = pdf_path
        except Exception as e:
            logger.exception(f"Error generating PDF: {e.__class__.__name__}: {e}")
        try:
            from backend.utils import write_md_to_word
            await write_md_to_word(report)
            docx_path: Path = base_path.with_suffix(".docx")
            result["docx"] = docx_path
        except Exception as e:
            logger.exception(f"Error generating DOCX: {e.__class__.__name__}: {e}")
        return result
    except Exception as e:
        logger.exception(f"Error generating report files: {e.__class__.__name__}: {e}")
        return {"md": Path(f"reports/{base_filename}.md")}


async def send_file_paths(
    websocket: ServerWebSocket,
    file_paths: dict[str, Path],
):
    await websocket.send_json(
        {
            "type": "path",
            "output": str(file_paths),
        }
    )


def get_config_dict(
    langchain_api_key: str | None = None,
    openai_api_key: str | None = None,
    tavily_api_key: str | None = None,
    google_api_key: str | None = None,
    google_cx_key: str | None = None,
    bing_api_key: str | None = None,
    searchapi_api_key: str | None = None,
    serpapi_api_key: str | None = None,
    serper_api_key: str | None = None,
    searx_url: str | None = None,
) -> dict[str, str]:
    return {
        "BING_API_KEY": str(bing_api_key or os.getenv("BING_API_KEY", "") or "").strip(),
        "DOC_PATH": str(os.getenv("DOC_PATH", "./my-docs") or "").strip(),
        "EMBEDDING_MODEL": str(os.getenv("OPENAI_EMBEDDING_MODEL", "") or "").strip(),
        "GOOGLE_API_KEY": str(google_api_key or os.getenv("GOOGLE_API_KEY", "") or "").strip(),
        "GOOGLE_CX_KEY": str(google_cx_key or os.getenv("GOOGLE_CX_KEY", "") or "").strip(),
        "LANGCHAIN_API_KEY": str(langchain_api_key or os.getenv("LANGCHAIN_API_KEY", "") or "").strip(),
        "LANGCHAIN_TRACING_V2": str(os.getenv("LANGCHAIN_TRACING_V2", "true") or "").strip(),
        "OPENAI_API_KEY": str(openai_api_key or os.getenv("OPENAI_API_KEY", "") or "").strip(),
        "RETRIEVER": str(os.getenv("RETRIEVER", "") or "").strip(),
        "SEARCHAPI_API_KEY": str(searchapi_api_key or os.getenv("SEARCHAPI_API_KEY", "") or "").strip(),
        "SEARX_URL": str(searx_url or os.getenv("SEARX_URL", "") or "").strip(),
        "SERPAPI_API_KEY": str(serpapi_api_key or os.getenv("SERPAPI_API_KEY", "") or "").strip(),
        "SERPER_API_KEY": str(serper_api_key or os.getenv("SERPER_API_KEY", "") or "").strip(),
        "TAVILY_API_KEY": str(tavily_api_key or os.getenv("TAVILY_API_KEY", "") or "").strip(),
    }


def update_environment_variables(
    config: dict[str, str],
) -> None:
    for key, value in config.items():
        os.environ[str(key or "").strip()] = str(value or "").strip()


async def handle_file_upload(
    file: UploadFile,
    DOC_PATH: os.PathLike | str,
) -> dict[str, str]:
    if not file.filename:
        return {"message": "No file uploaded"}
    filename: str = secure_filename(file.filename)
    file_path: Path = Path(DOC_PATH, filename).absolute()
    file_path.write_bytes(await file.read())
    logger.debug(f"File uploaded to '{file_path}'")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {
        "filename": str(filename or "").strip(),
        "path": str(file_path or "").strip(),
    }


async def handle_file_deletion(
    filename: str,
    DOC_PATH: os.PathLike | str,
) -> JSONResponse:
    file_path: Path = Path(DOC_PATH, os.path.basename(str(filename or "").strip())).absolute()
    if file_path.exists() and file_path.is_file():
        file_path.unlink(missing_ok=True)
        logger.debug(f"File deleted: '{file_path}'")
        return JSONResponse({"message": "File deleted successfully"}, status_code=200)
    else:
        logger.error(f"File not found: '{file_path}'")
        return JSONResponse(
            {"message": "File not found"},
            status_code=404,
        )


async def execute_multi_agents(
    manager: WebSocketManager,
) -> JSONResponse:
    websocket: ServerWebSocket | HTTPStreamAdapter | None = next(iter(manager.active_connections), None)
    if websocket:
        from multi_agents.main import run_research_task
        report: str = await run_research_task(
            "Is AI in a hype cycle?",
            websocket=websocket,
            stream_output=stream_output,
        )
        return JSONResponse({"report": report}, status_code=200)
    else:
        return JSONResponse({"message": "No active ServerWebSocket connection"}, status_code=400)


async def handle_websocket_communication(
    websocket: ServerWebSocket,
    manager: WebSocketManager,
) -> None:
    running_task: asyncio.Task | None = None

    def run_long_running_task(awaitable: Awaitable) -> asyncio.Task:
        async def safe_run():
            try:
                await awaitable
            except asyncio.CancelledError:
                logger.info("Task cancelled.")
                raise
            except Exception as e:
                logger.error(f"Error running task: {e}\n{traceback.format_exc()}")
                await websocket.send_json({
                    "type": "logs",
                    "content": "error",
                    "output": f"Error: {e}",
                })
        return asyncio.create_task(safe_run())

    try:
        while True:
            try:
                data: str = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
                elif running_task and not running_task.done():
                    logger.warning(
                        f"Received request while task is already running. Request data preview: {data[:min(20, len(data))]}..."
                    )
                    await websocket.send_json({
                        "type": "logs",
                        "output": "Task already running. Please wait.",
                    })
                elif data.startswith("start"):
                    running_task = run_long_running_task(handle_start_command(websocket, data, manager))
                elif data.startswith("human_feedback"):
                    running_task = run_long_running_task(handle_human_feedback(data))
                elif data.startswith("chat"):
                    running_task = run_long_running_task(handle_chat(websocket, data, manager))
                else:
                    logger.error("Error in handle_websocket_communication: Unknown command or not enough parameters provided.")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    finally:
        if running_task and not running_task.done():
            running_task.cancel()


def extract_command_data(
    json_data: dict[str, Any],
) -> tuple[str, str, list[str], list[str], Tone, dict[str, str], str, list[str]]:
    return (
        str(json_data.get("task") or "").strip(),
        str(json_data.get("report_type") or "").strip(),
        [str(url or "").strip() for url in json_data.get("source_urls", [])],
        [str(url or "").strip() for url in json_data.get("document_urls", [])],
        Tone.__members__[str(json_data.get("tone") or "").strip()],
        json_data.get("headers", {}),
        str(json_data.get("report_source") or "").strip(),
        [str(domain or "").strip() for domain in json_data.get("query_domains", [])],
    )


async def get_report_file_urls(
    report: str,
    base_filename: str,
) -> dict[str, Any]:
    """Generate report files and return their URLs."""
    file_paths: dict[str, Path] = await generate_report_files(report, base_filename)
    file_urls: dict[str, str] = {}
    for format_name, file_path in file_paths.items():
        try:
            relative_path: Path = file_path.relative_to(Path.cwd())
            url: str = f"/{relative_path.as_posix()}"
            file_urls[format_name] = url
        except Exception as e:
            logger.error(f"Error converting path to URL for {format_name}: {e}")
            file_urls[format_name] = str(file_path)
    return {
        "type": "report_complete",
        "content": report,
        "files": file_urls,
        "base_filename": base_filename
    }


def validate_config_file(content: bytes) -> bool:
    """Validate the uploaded config file.

    Args:
        content: The content of the config file.

    Returns:
        bool: True if the config file is valid, False otherwise.
    """
    try:
        config_dict = json.loads(content.decode("utf-8"))
        if not isinstance(config_dict, dict):
            logger.error("Config file is not a dictionary")
            return False

        expected_keys: list[str] = ["REPORT_TYPE", "REPORT_FORMAT", "LANGUAGE", "TONE"]
        if not any(key in config_dict for key in expected_keys):
            logger.error(f"Config file is missing expected keys: {expected_keys}")
            return False

        return True
    except json.JSONDecodeError as e:
        logger.exception(f"Invalid JSON in config file: {e.__class__.__name__}: {e}")
        return False
    except Exception as e:
        logger.exception(f"Error validating config file: {e.__class__.__name__}: {e}")
        return False


def save_config_file(
    content: bytes,
    config_path: Path,
) -> bool:
    """Save a config file if it's valid.

    Args:
        content: The content of the config file.
        config_path: The path to save the config file.

    Returns:
        bool: True if the config file was saved successfully, False otherwise.
    """
    if validate_config_file(content):
        try:
            config_path.write_bytes(content)
            logger.info(f"Uploaded config file saved to {config_path}")
            return True
        except Exception as e:
            logger.exception(f"Error saving config file: {e.__class__.__name__}: {e}")
            return False
    else:
        logger.error("Invalid config file")
        return False


def save_uploaded_file(
    filename: str,
    content: bytes,
    upload_dir: Path,
) -> str:
    """Save an uploaded file.

    Args:
        filename: The name of the file.
        content: The content of the file.
        upload_dir: The directory to save the file in.

    Returns:
        str: The path to the saved file.
    """
    file_path: Path = upload_dir / filename
    file_path.parent.mkdir(exist_ok=True, parents=True)
    file_path.write_bytes(content)
    return str(file_path)


def get_file_content(file_path: str) -> tuple[bytes, int, str]:
    """Get the content of a file.

    Args:
        file_path: The path to the file.

    Returns:
        tuple: The file content, size, and content type.
    """
    import mimetypes
    path: Path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    file_size: int = path.stat().st_size
    data: bytes = path.read_bytes()
    ext: str = os.path.splitext(path)[1]
    content_type: str | None = mimetypes.guess_type(path)[0]
    if not content_type and ext in mimetypes.types_map:
        content_type = mimetypes.types_map[ext]
    if not content_type:
        content_type = "application/octet-stream"
    return data, file_size, content_type


def get_default_prompt_templates() -> dict[str, str]:
    """Get default prompt templates from the Config class."""
    default_config: dict[str, Any] = Config.default_config_dict()
    return {k: v for k, v in default_config.items() if k.startswith("PROMPT_")}
