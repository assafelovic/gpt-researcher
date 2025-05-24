from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import time
import traceback

from datetime import datetime
from typing import Any, Awaitable

from fastapi import UploadFile, WebSocket
from fastapi.responses import JSONResponse
from gpt_researcher import GPTResearcher
from gpt_researcher.document.document import DocumentLoader

from backend.server.websocket_manager import WebSocketManager
from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CustomLogsHandler:
    """Custom handler to capture streaming logs from the research process"""

    def __init__(
        self,
        websocket: WebSocket | None,
        task: str,
    ):
        self.logs: list[dict[str, Any]] = []
        self.websocket: WebSocket | None = websocket
        sanitized_filename: str = sanitize_filename(f"task_{int(time.time())}_{task}")
        self.log_file: str = os.path.join("outputs", f"{sanitized_filename}.json")
        self.timestamp: str = datetime.now().isoformat()
        # Initialize log file with metadata
        os.makedirs("outputs", exist_ok=True)
        with open(self.log_file, "w") as f:
            json.dump(
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
                f,
                indent=2,
            )

    async def send_json(self, data: dict[str, Any]) -> None:
        """Store log data and send to websocket"""
        # Send to websocket for real-time display
        if self.websocket is not None:
            await self.websocket.send_json(data)

        # Read current log file
        with open(self.log_file, "r") as f:
            log_data: dict[str, Any] = json.load(f)

        # Update appropriate section based on data type
        if data.get("type") == "logs":
            events: list[dict[str, Any]] = log_data.get("events", [])
            events.append({"timestamp": datetime.now().isoformat(), "type": "event", "data": data})
            log_data["events"] = events
        else:
            # Update content section for other types of data
            content: dict[str, Any] = log_data.get("content", {})
            content.update(data)
            log_data["content"] = content

        # Save updated log file
        with open(self.log_file, "w") as f:
            json.dump(log_data, f, indent=2)
        logger.debug(f"Log entry written to: {self.log_file}")


class Researcher:
    def __init__(
        self,
        query: str,
        report_type: str = "research_report",
    ):
        self.query: str = query
        self.report_type: str = report_type
        # Generate unique ID for this research task
        self.research_id: str = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query)}"
        # Initialize logs handler with research ID
        self.logs_handler: CustomLogsHandler = CustomLogsHandler(None, self.research_id)
        self.researcher: GPTResearcher = GPTResearcher(
            query=query,
            report_type=report_type,
            websocket=self.logs_handler,
        )

    async def research(self) -> dict[str, Any]:
        """Conduct research and return paths to generated files"""
        await self.researcher.conduct_research()
        report: str = await self.researcher.write_report()

        # Generate the files
        sanitized_filename: str = sanitize_filename(f"task_{int(time.time())}_{self.query}")
        file_paths: dict[str, str] = await generate_report_files(report, sanitized_filename)

        # Get the JSON log path that was created by CustomLogsHandler
        json_relative_path: str = os.path.relpath(self.logs_handler.log_file)

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
    # 255 - len(os.getcwd()) - len("\\gpt-researcher\\outputs\\") - len("task_") - len(timestamp) - len("_.json") - safety_margin
    max_task_length: int = 255 - len(os.getcwd()) - 24 - 5 - 10 - 6 - 5  # ~189 chars for task

    # Truncate task if needed
    truncated_task: str = task[:max_task_length] if len(task) > max_task_length else task

    # Reassemble and clean the filename
    sanitized: str = f"{prefix}_{timestamp}_{truncated_task}"
    return re.sub(r"[^\w\s-]", "", sanitized).strip()


async def handle_start_command(
    websocket: WebSocket,
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

    if not (task or "").strip() or not (report_type or "").strip():
        print("Error: Missing `task` or `report_type`")
        return

    # Create logs handler with websocket and task
    logs_handler = CustomLogsHandler(websocket, task)
    # Initialize log content with query
    await logs_handler.send_json(
        {
            "query": task,
            "sources": [],
            "context": [],
            "report": "",
        }
    )

    sanitized_filename: str = sanitize_filename(f"task_{int(time.time())}_{task}")

    report: str = await manager.start_streaming(
        task,
        report_type,
        report_source,
        source_urls,
        document_urls,
        tone,
        websocket,
        headers,
        query_domains=query_domains,
    )
    report = str(report)
    file_paths: dict[str, str] = await generate_report_files(report, sanitized_filename)
    # Add JSON log path to file_paths
    file_paths["json"] = os.path.relpath(logs_handler.log_file)
    await send_file_paths(websocket, file_paths)


async def handle_human_feedback(
    data: str,
):
    feedback_data = json.loads(data[14:])  # Remove "human_feedback" prefix
    print(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state


async def handle_chat(
    websocket: WebSocket,
    data: str,
    manager: WebSocketManager,
):
    json_data = json.loads(data[4:])
    print(f"Received chat message: {json_data.get('message')}")
    await manager.chat(json_data.get("message"), websocket)


async def generate_report_files(report: str, filename: str) -> dict[str, str]:
    pdf_path = await write_md_to_pdf(report, filename)
    docx_path = await write_md_to_word(report, filename)
    md_path = await write_text_to_md(report, filename)
    return {"pdf": pdf_path, "docx": docx_path, "md": md_path}


async def send_file_paths(
    websocket: WebSocket,
    file_paths: dict[str, str],
):
    await websocket.send_json({"type": "path", "output": file_paths})


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
        "LANGCHAIN_API_KEY": langchain_api_key or os.getenv("LANGCHAIN_API_KEY", ""),
        "OPENAI_API_KEY": openai_api_key or os.getenv("OPENAI_API_KEY", ""),
        "TAVILY_API_KEY": tavily_api_key or os.getenv("TAVILY_API_KEY", ""),
        "GOOGLE_API_KEY": google_api_key or os.getenv("GOOGLE_API_KEY", ""),
        "GOOGLE_CX_KEY": google_cx_key or os.getenv("GOOGLE_CX_KEY", ""),
        "BING_API_KEY": bing_api_key or os.getenv("BING_API_KEY", ""),
        "SEARCHAPI_API_KEY": searchapi_api_key or os.getenv("SEARCHAPI_API_KEY", ""),
        "SERPAPI_API_KEY": serpapi_api_key or os.getenv("SERPAPI_API_KEY", ""),
        "SERPER_API_KEY": serper_api_key or os.getenv("SERPER_API_KEY", ""),
        "SEARX_URL": searx_url or os.getenv("SEARX_URL", ""),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
        "DOC_PATH": os.getenv("DOC_PATH", "./my-docs"),
        "RETRIEVER": os.getenv("RETRIEVER", ""),
        "EMBEDDING_MODEL": os.getenv("OPENAI_EMBEDDING_MODEL", ""),
    }


def update_environment_variables(config: dict[str, str]):
    for key, value in config.items():
        os.environ[key] = value


async def handle_file_upload(
    file: UploadFile,
    DOC_PATH: str,
) -> dict[str, str]:
    filename: str = file.filename or ""
    file_path: str = os.path.join(DOC_PATH, os.path.basename(filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"File uploaded to {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": filename, "path": file_path}


async def handle_file_deletion(filename: str, DOC_PATH: str) -> JSONResponse:
    file_path: str = os.path.join(DOC_PATH, os.path.basename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File deleted: {file_path}")
        return JSONResponse(content={"message": "File deleted successfully"})
    else:
        print(f"File not found: {file_path}")
        return JSONResponse(status_code=404, content={"message": "File not found"})


async def execute_multi_agents(
    manager: WebSocketManager,
) -> Any:
    websocket: WebSocket | None = manager.active_connections[0] if manager.active_connections else None
    if websocket:
        from multi_agents.main import run_research_task

        report: str = await run_research_task(
            "Is AI in a hype cycle?",
            websocket,
            stream_output=True,
        )
        return {"report": report}
    else:
        return JSONResponse(status_code=400, content={"message": "No active WebSocket connection"})


async def handle_websocket_communication(
    websocket: WebSocket,
    manager: WebSocketManager,
):
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
                await websocket.send_json(
                    {
                        "type": "logs",
                        "content": "error",
                        "output": f"Error: {e}",
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
                    # discard any new request if a task is already running
                    logger.warning(f"Received request while task is already running. Request data preview: {data[: min(20, len(data))]}...")
                    _ = websocket.send_json(
                        {
                            "types": "logs",
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
                    print("Error: Unknown command or not enough parameters provided.")
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
    finally:
        if running_task and not running_task.done():
            running_task.cancel()


def extract_command_data(
    json_data: dict[str, Any],
) -> tuple[str | None, str | None, list[str] | None, list[str] | None, str | None, dict[str, str] | None, str | None, list[str] | None]:
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
