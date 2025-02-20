from __future__ import annotations

import json
import logging
import os
import re

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import UploadFile
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket as ServerWebSocket  # pyright: ignore[reportMissingImports]
from gpt_researcher.actions import stream_output
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.config import Config
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.utils.schemas import ReportType, Tone
from multi_agents.main import run_research_task
from werkzeug.utils import secure_filename

from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md

if TYPE_CHECKING:
    from backend.server.websocket_manager import WebSocketManager

logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger(__name__)


class CustomLogsHandler:
    """Custom handler to capture streaming logs from the research process."""

    def __init__(
        self,
        websocket: ServerWebSocket,
        task: str | None = None,
    ):
        self.websocket: ServerWebSocket = websocket
        self.logs: list[dict[str, Any]] = []
        self.timestamp: str = datetime.now().isoformat()

        # Initialize log file with metadata
        sanitized_filename: str = sanitize_filename(
            f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{task}"
        )
        self.log_file: Path = Path(
            os.path.expandvars(
                os.path.join(
                    "outputs",
                    f"{sanitized_filename}.json",
                )
            )
        ).absolute()
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
        # Send to websocket for real-time display
        await self.websocket.send_json(data)

        # Read current log file
        log_data = json.loads(self.log_file.read_text().strip())

        # Update appropriate section based on data type
        if data.get("type") == "logs":
            events_list: list[dict[str, Any]] = log_data["events"]
            events_list.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "event",
                    "data": data,
                }
            )
        else:
            # Update content section for other types of data
            content_dict: dict[str, Any] = log_data["content"]
            content_dict.update(data)

        # Save updated log file
        self.log_file.write_text(json.dumps(log_data, indent=2))
        logger.debug(f"Log entry written to: '{self.log_file}'")


class Researcher:
    def __init__(
        self,
        query: str,
        report_type: str = "research_report",
        websocket: CustomLogsHandler | ServerWebSocket | None = None,
    ):
        self.query: str = query
        self.report_type: str = report_type
        # Generate unique ID for this research task
        self.research_id: str = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query)}"
        # Initialize logs handler with research ID
        self.logs_handler: CustomLogsHandler | None = None
        if isinstance(websocket, ServerWebSocket):  # fastapi
            self.logs_handler = CustomLogsHandler(
                websocket=websocket,
                task=self.query,
            )
        elif isinstance(websocket, CustomLogsHandler):  # flask-socketio
            self.logs_handler = websocket
        else:
            raise ValueError("Invalid websocket type")

        self.researcher: GPTResearcher = GPTResearcher(
            query=query,
            config=Config(REPORT_TYPE=ReportType(self.report_type)),
            websocket=self.logs_handler,
        )

    async def research(self) -> dict:
        """Conduct research and return paths to generated files."""
        await self.researcher.conduct_research()
        report: str = await self.researcher.write_report()

        # Generate the files
        sanitized_filename: str = sanitize_filename(
            f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.query}"
        )
        file_paths: dict[str, Path] = await generate_report_files(
            report,
            sanitized_filename,
        )

        # Get the JSON log path that was created by CustomLogsHandler
        if self.logs_handler and self.logs_handler.log_file:
            json_relative_path: Path = self.logs_handler.log_file.relative_to(Path.cwd().absolute())
        else:
            json_relative_path: Path = Path("")

        return {
            "output": {
                **file_paths,  # Include PDF, DOCX, and MD paths
                "json": json_relative_path,
            }
        }


def sanitize_filename(
    filename: str,
) -> str:
    # Split into components
    prefix, timestamp, *task_parts = filename.split("_")
    task = "_".join(task_parts)

    # Calculate max length for task portion
    # 255 - len("outputs/") - len("task_") - len(timestamp) - len("_.json") - safety_margin
    max_task_length = 255 - 8 - 5 - 10 - 6 - 10  # ~216 chars for task

    # Truncate task if needed
    truncated_task = task[:max_task_length] if len(task) > max_task_length else task

    # Reassemble and clean the filename
    sanitized = f"{prefix}_{timestamp}_{truncated_task}"
    return re.sub(r"[^\w\s-]", "", sanitized).strip()


async def handle_start_command(
    websocket: ServerWebSocket,
    data: str,
    manager: WebSocketManager,
):
    json_data: dict[str, Any] = json.loads(data[6:])
    task: str | None = json_data.get("task")
    report_type: str | None = json_data.get("report_type")
    source_urls: list[str] | None = json_data.get("source_urls")
    document_urls: list[str] | None = json_data.get("document_urls")
    tone: str | None = json_data.get("tone")
    headers: dict[str, Any] | None = json_data.get("headers")
    report_source: str | None = json_data.get("report_source")

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
        task=task or "",
        report_type=report_type or "",
        report_source=report_source or "",
        source_urls=source_urls or [],
        document_urls=document_urls or [],
        tone=tone or Tone.Objective,
        websocket=websocket,
        headers=headers,
    )
    sanitized_filename: str = sanitize_filename(f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{task}")
    # Generate the files
    file_paths: dict[str, Path] = await generate_report_files(
        report,
        sanitized_filename,
    )
    # Add JSON log path to file_paths
    file_paths["json"] = logs_handler.log_file.relative_to(Path.cwd().absolute())
    await send_file_paths(
        websocket=websocket,
        file_paths=file_paths,
    )


async def handle_human_feedback(
    data: str,
):
    feedback_data = json.loads(data[14:])  # Remove "human_feedback" prefix
    logger.debug(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state


async def handle_chat(
    websocket: ServerWebSocket,
    data: str,
    manager: WebSocketManager,
) -> str | None:
    json_data: dict[str, Any] = json.loads(data[4:])
    logger.debug(f"Received chat message: {json_data['message']}")
    return await manager.chat(json_data["message"], websocket)


async def generate_report_files(
    report: str,
    filename: str,
) -> dict[str, Path]:
    pdf_path = await write_md_to_pdf(report, filename)
    docx_path = await write_md_to_word(report, filename)
    md_path = await write_text_to_md(report, filename)
    return {
        "pdf": Path(os.path.expandvars(os.path.normpath(pdf_path))).absolute(),
        "docx": Path(os.path.expandvars(os.path.normpath(docx_path))).absolute(),
        "md": Path(os.path.expandvars(os.path.normpath(md_path))).absolute(),
    }


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
    langchain_api_key: str,
    openai_api_key: str,
    tavily_api_key: str,
    google_api_key: str,
    google_cx_key: str,
    bing_api_key: str,
    searchapi_api_key: str,
    serpapi_api_key: str,
    serper_api_key: str,
    searx_url: str,
) -> dict[str, str]:
    return {
        "BING_API_KEY": bing_api_key or os.getenv("BING_API_KEY", ""),
        "DOC_PATH": os.getenv("DOC_PATH", "./my-docs"),
        "EMBEDDING_MODEL": os.getenv("OPENAI_EMBEDDING_MODEL", ""),
        "GOOGLE_API_KEY": google_api_key or os.getenv("GOOGLE_API_KEY", ""),
        "GOOGLE_CX_KEY": google_cx_key or os.getenv("GOOGLE_CX_KEY", ""),
        "LANGCHAIN_API_KEY": langchain_api_key or os.getenv("LANGCHAIN_API_KEY", ""),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
        "OPENAI_API_KEY": openai_api_key or os.getenv("OPENAI_API_KEY", ""),
        "RETRIEVER": os.getenv("RETRIEVER", ""),
        "SEARCHAPI_API_KEY": searchapi_api_key or os.getenv("SEARCHAPI_API_KEY", ""),
        "SEARX_URL": searx_url or os.getenv("SEARX_URL", ""),
        "SERPAPI_API_KEY": serpapi_api_key or os.getenv("SERPAPI_API_KEY", ""),
        "SERPER_API_KEY": serper_api_key or os.getenv("SERPER_API_KEY", ""),
        "TAVILY_API_KEY": tavily_api_key or os.getenv("TAVILY_API_KEY", ""),
    }


def update_environment_variables(
    config: dict[str, str],
) -> None:
    for key, value in config.items():
        os.environ[key] = value


async def handle_file_upload(
    file: UploadFile,
    DOC_PATH: os.PathLike | str,
) -> dict[str, str]:
    if not file.filename:
        return {"message": "No file uploaded"}
    filename: str = secure_filename(file.filename)
    file_path: str = os.path.join(DOC_PATH, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logger.debug(f"File uploaded to {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": filename, "path": file_path}


async def handle_file_deletion(
    filename: str,
    DOC_PATH: os.PathLike | str,
) -> JSONResponse:
    file_path = os.path.join(DOC_PATH, os.path.basename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.debug(f"File deleted: {file_path}")
        return JSONResponse({"message": "File deleted successfully"})
    else:
        logger.error(f"File not found: {file_path}")
        return JSONResponse({"message": "File not found"}, status_code=404)


async def execute_multi_agents(
    manager: WebSocketManager,
) -> Any:
    websocket: ServerWebSocket | None = next(iter(manager.active_connections), None)
    if websocket:
        report: str = await run_research_task(
            "Is AI in a hype cycle?",
            websocket=websocket,
            stream_output=stream_output,
        )
        return {"report": report}
    else:
        return JSONResponse({"message": "No active ServerWebSocket connection"}), 400


async def handle_websocket_communication(
    websocket: ServerWebSocket,
    manager: WebSocketManager,
):
    data: str = await websocket.receive_text()
    if data.startswith("start"):
        await handle_start_command(websocket, data, manager)
    elif data.startswith("human_feedback"):
        await handle_human_feedback(data)
    elif data.startswith("chat"):
        await handle_chat(websocket, data, manager)
    else:
        logger.error("Error in handle_websocket_communication: Unknown command or not enough parameters provided.")


def extract_command_data(
    json_data: dict[str, Any],
) -> tuple:
    return (
        json_data.get("document_urls"),
        json_data.get("headers", {}),
        json_data.get("report_source"),
        json_data.get("report_type"),
        json_data.get("source_urls"),
        json_data.get("task"),
        json_data.get("tone"),
    )
