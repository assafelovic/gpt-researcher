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
from typing import TYPE_CHECKING, Any, Awaitable

from fastapi import UploadFile, WebSocket
from fastapi.responses import JSONResponse
from gpt_researcher import GPTResearcher
from gpt_researcher.document.document import DocumentLoader

from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md

logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.server.websocket_manager import WebSocketManager


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
            log_data["content"].update(data)

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
    max_task_length = 255 - len(os.getcwd()) - 24 - 5 - 10 - 6 - 5  # ~189 chars for task

    # Truncate task if needed (by bytes)
    truncated_task = ""
    byte_count = 0
    for char in task:
        char_bytes = len(char.encode('utf-8'))
        if byte_count + char_bytes <= max_task_length:
            truncated_task += char
            byte_count += char_bytes
        else:
            break

    # Reassemble and clean the filename
    sanitized = f"{prefix}_{timestamp}_{truncated_task}"
    return re.sub(r"[^\w-]", "", sanitized).strip()


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
        mcp_enabled,
        mcp_strategy,
        mcp_configs,
    ) = extract_command_data(json_data)

    if not (task or "").strip() or not (report_type or "").strip():
        print("❌ Error: Missing task or report_type")
        await websocket.send_json({
            "type": "logs",
            "content": "error",
            "output": f"Missing required parameters - task: {task}, report_type: {report_type}"
        })
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
        query_domains,
        mcp_enabled,
        mcp_strategy,
        mcp_configs,
    )
    report = str(report)
    file_paths: dict[str, str] = await generate_report_files(report, sanitized_filename)
    # Add JSON log path to file_paths
    file_paths["json"] = os.path.relpath(logs_handler.log_file)
    await send_file_paths(websocket, file_paths)


async def handle_human_feedback(
    data: str,
):
    """Handle human feedback.

    Args:
        data (str): The data to handle.
    """
    feedback_data: dict[str, Any] = json.loads(data[14:])  # Remove "human_feedback" prefix
    print(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state


async def handle_chat(
    websocket: WebSocket,
    data: str,
    manager: WebSocketManager,
):
    json_data: dict[str, Any] = json.loads(data[4:])
    print(f"Received chat message: {json_data.get('message')}")
    logger.info(f"Received chat message: {json_data.get('message')}")
    await manager.chat(json_data.get("message"), websocket)


async def generate_report_files(report: str, filename: str) -> dict[str, str]:
    filename = filename.replace(" ", "_")
    pdf_path: str = await write_md_to_pdf(report, filename)
    docx_path: str = await write_md_to_word(report, filename)
    md_path: str = await write_text_to_md(report, filename)
    return {
        "pdf": pdf_path,
        "docx": docx_path,
        "md": md_path,
    }


async def send_file_paths(
    websocket: WebSocket,
    file_paths: dict[str, str],
):
    await websocket.send_json({"type": "path", "output": file_paths})


def get_config_dict(
    *args,
    **kwargs: Any,
) -> dict[str, str]:
    positional_argnames: list[str] = [
        "langchain_api_key",
        "openai_api_key",
        "tavily_api_key",
        "google_api_key",
        "google_cx_key",
        "bing_api_key",
        "searchapi_api_key",
        "serpapi_api_key",
        "serper_api_key",
        "searx_url",
    ]
    for i, arg in enumerate(positional_argnames):
        kwargs[arg] = args[i] if i < len(args) else None
    return {
        "BING_API_KEY": kwargs.get("bing_api_key", os.getenv("BING_API_KEY", "")),
        "BRAVE_API_KEY": kwargs.get("brave_api_key", os.getenv("BRAVE_API_KEY", "")),
        "DOC_PATH": kwargs.get("doc_path", os.getenv("DOC_PATH", "./my-docs")),
        "EMBEDDING_MODEL": kwargs.get("embedding_model", os.getenv("OPENAI_EMBEDDING_MODEL", "")),
        "GOOGLE_API_KEY": kwargs.get("google_api_key", os.getenv("GOOGLE_API_KEY", "")),
        "GOOGLE_CX_KEY": kwargs.get("google_cx_key", os.getenv("GOOGLE_CX_KEY", "")),
        "LANGCHAIN_API_KEY": kwargs.get("langchain_api_key", os.getenv("LANGCHAIN_API_KEY", "")),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
        "OPENAI_API_KEY": kwargs.get("openai_api_key", os.getenv("OPENAI_API_KEY", "")),
        "RETRIEVER": kwargs.get("retriever", os.getenv("RETRIEVER", "")),
        "SEARCHAPI_API_KEY": kwargs.get("searchapi_api_key", os.getenv("SEARCHAPI_API_KEY", "")),
        "SEARX_URL": kwargs.get("searx_url", os.getenv("SEARX_URL", "")),
        "SERPAPI_API_KEY": kwargs.get("serpapi_api_key", os.getenv("SERPAPI_API_KEY", "")),
        "SERPER_API_KEY": kwargs.get("serper_api_key", os.getenv("SERPER_API_KEY", "")),
        "TAVILY_API_KEY": kwargs.get("tavily_api_key", os.getenv("TAVILY_API_KEY", "")),
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
    print(f"File uploaded to '{file_path}'")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": filename, "path": file_path}


async def handle_file_deletion(
    filename: str,
    DOC_PATH: str,
) -> JSONResponse:
    """Handle file deletion.

    Args:
        filename (str): The name of the file to delete.
        DOC_PATH (str): The path to the directory containing the file.

    Returns:
        JSONResponse: The response to the request.
    """
    file_path: str = os.path.join(DOC_PATH, os.path.basename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File deleted: '{file_path}'")
        return JSONResponse(content={"message": "File deleted successfully"})
    else:
        print(f"File not found: '{file_path}'")
        return JSONResponse(status_code=404, content={"message": "File not found"})


async def execute_multi_agents(
    manager: WebSocketManager,
) -> Any:
    """Execute the multi-agents research task.

    Args:
        manager (WebSocketManager): The manager for the WebSocket connection.

    Returns:
        Any: The response to the request.
    """
    websocket: WebSocket | None = (
        manager.active_connections[0]
        if manager.active_connections
        else None
    )
    if websocket is not None:
        from multi_agents.main import run_research_task

        report: str = await run_research_task(
            "Is AI in a hype cycle?",
            websocket,
            stream_output=True,
        )
        return {"report": report}
    else:
        return JSONResponse(
            status_code=400,
            content={"message": "No active WebSocket connection"},
        )


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
                logger.error(f"Error running task: {e.__class__.__name__}: {e}\n{traceback.format_exc()}")
                print(f"Error running task: {e.__class__.__name__}: {e}\n{traceback.format_exc()}")
                await websocket.send_json(
                    {
                        "type": "logs",
                        "content": "error",
                        "output": f"Error: {e.__class__.__name__}: {e}\n{traceback.format_exc()}",
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
                    print(f"Error: Unknown command or not enough parameters provided. ```\n{data}\n```. Expected: 'start', 'human_feedback', 'chat'")
            except Exception as e:
                print(f"WebSocket error: {e.__class__.__name__}: {e}")
                break
    finally:
        if running_task and not running_task.done():
            running_task.cancel()


def extract_command_data(
    json_data: dict[str, Any],
) -> tuple[
    str | None,  # task
    str | None,  # report_type
    list[str] | None,  # source_urls
    list[str] | None,  # document_urls
    str | None,  # tone
    dict[str, str] | None,  # headers
    str | None,  # report_source
    list[str] | None,  # query_domains
]:
    return (
        json_data.get("task"),
        json_data.get("report_type"),
        json_data.get("source_urls"),
        json_data.get("document_urls"),
        json_data.get("tone"),
        json_data.get("headers", {}),
        json_data.get("report_source"),
        json_data.get("query_domains", []),
        json_data.get("mcp_enabled", False),
        json_data.get("mcp_strategy", "fast"),
        json_data.get("mcp_configs", []),
    )
