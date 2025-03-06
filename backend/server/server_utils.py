from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import traceback

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable

from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket as ServerWebSocket
from gpt_researcher.actions import stream_output
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.config import Config
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.utils.enum import ReportType, Tone
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.utils.schemas import LogHandler

from backend.server.websocket_manager import WebSocketManager

logger: logging.Logger = get_formatted_logger("gpt_researcher")


class CustomLogsHandler(LogHandler):
    """Custom handler to capture streaming logs from the research process."""

    def __init__(
        self,
        websocket: ServerWebSocket | None = None,
        task: str | None = None,
    ):
        self.websocket: ServerWebSocket | None = websocket
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

    async def on_tool_start(self, tool_name: str, **kwargs: Any) -> None:
        logger.debug(f"Tool start: {tool_name}")

    async def on_agent_action(self, action: str, **kwargs: Any) -> None:
        logger.debug(f"Agent action: {action}")

    async def on_research_step(self, step: str, details: dict[str, Any], **kwargs: Any) -> None:
        logger.debug(f"Research step: {step}")


class Researcher:
    def __init__(
        self,
        query: str,
        report_type: str | ReportType = ReportType.ResearchReport,
        websocket: CustomLogsHandler | ServerWebSocket | None = None,
        config: Config | None = None,
    ):
        self.query: str = str(query or "").strip()
        self.report_type: ReportType = (
            ReportType.__members__[report_type.lower().title()] if isinstance(report_type, str) else report_type
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
            config=Config(REPORT_TYPE=self.report_type) if config is None else config,
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
        file_paths: dict[str, str] = await generate_report_files(report, sanitized_filename)

        if self.logs_handler is not None and self.logs_handler.log_file.exists() and self.logs_handler.log_file.is_file():
            json_relative_path: str = str(self.logs_handler.log_file.relative_to(Path.cwd().absolute()))
        else:
            json_relative_path: str = f"{sanitized_filename}.json"

        return {
            "output": {
                **file_paths,  # Include PDF, DOCX, and MD paths
                "json": json_relative_path,
            }
        }


def sanitize_filename(filename: str) -> str:
    # Split into components
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
    """Handle start command from the websocket."""
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

    sanitized_filename: str = sanitize_filename(
        f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(task or '').strip()}"
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
    file_paths: dict[str, str] = await generate_report_files(
        str(report or "").strip(),
        str(sanitized_filename or "").strip(),
    )
    # Add JSON log path to file_paths
    file_paths["json"] = os.path.relpath(logs_handler.log_file)
    await send_file_paths(websocket, file_paths)


async def handle_human_feedback(data: str) -> None:
    feedback_data: dict[str, Any] = json.loads(data[14:])  # Remove "human_feedback" prefix
    logger.debug(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state


async def handle_chat(websocket, data: str, manager):
    json_data = json.loads(data[4:])
    print(f"Received chat message: {json_data.get('message')}")
    await manager.chat(json_data.get("message"), websocket)


async def generate_report_files(
    report: str,
    filename: str,
) -> dict[str, str]:
    """Generate report files in different formats.

    Args:
        report: The report content in markdown format
        filename: The base filename to use for the reports

    Returns:
        A dictionary mapping format names to file paths
    """
    try:
        result: dict[str, str] = {}
        try:
            from backend.utils import write_text_to_md
            
            result["md"] = await write_text_to_md(report, filename)
        except Exception as e:
            logger.exception(f"Error generating MD: {e.__class__.__name__}: {e}")
        try:
            from backend.utils import write_md_to_pdf

            result["pdf"] = await write_md_to_pdf(report, filename)
        except Exception as e:
            logger.exception(f"Error generating PDF: {e.__class__.__name__}: {e}")
        try:
            from backend.utils import write_md_to_word

            result["docx"] = await write_md_to_word(report, filename)
        except Exception as e:
            logger.exception(f"Error generating DOCX: {e.__class__.__name__}: {e}")

    except Exception as e:
        logger.exception(f"Error generating report files: {e.__class__.__name__}: {e}")
        return {"md": f"reports/{filename}.md"}

    else:
        return result

async def send_file_paths(
    websocket: ServerWebSocket,
    file_paths: dict[str, Any],
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


async def handle_file_upload(file, DOC_PATH: str) -> dict[str, str]:
    file_path = os.path.join(DOC_PATH, os.path.basename(file.filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"File uploaded to {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": file.filename, "path": file_path}


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
    websocket: ServerWebSocket | None = next(iter(manager.active_connections), None)
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
                logger.error(f"Error running task: {traceback.format_exc()}")
                await websocket.send_json(
                    {
                        "type": "logs",
                        "content": "error",
                        "output": f"Error: {e.__class__.__name__}: {e}",
                    }
                )

        return asyncio.create_task(safe_run())

    try:
        while True:
            try:
                data: str = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
                elif running_task and not running_task.done():
                    logger.warning(
                        f"Received request while task is already running. Request data preview: {data[: min(20, len(data))]}..."
                    )
                    await websocket.send_json(
                        {
                            "type": "logs",
                            "output": "Task already running. Please wait.",
                        }
                    )
                elif data.startswith("start"):
                    running_task = run_long_running_task(handle_start_command(websocket, data, manager))
                elif data.startswith("human_feedback"):
                    running_task = run_long_running_task(handle_human_feedback(data))
                elif data.startswith("chat"):
                    running_task = run_long_running_task(handle_chat(websocket, data, manager))
                else:
                    logger.error(
                        "Error in handle_websocket_communication: Unknown command or not enough parameters provided."
                    )
            except Exception as e:
                logger.error(f"WebSocket error: {e.__class__.__name__}: {e}")
                break
    finally:
        if running_task and not running_task.done():
            running_task.cancel()


def extract_command_data(json_data: dict[str, Any]):
    return (
        json_data.get("task"),
        json_data.get("report_type"),
        json_data.get("source_urls"),
        json_data.get("document_urls"),
        json_data.get("tone"),
        json_data.get("headers", {}),
        json_data.get("report_source"),
        json_data.get("query_domains", []),
    )
