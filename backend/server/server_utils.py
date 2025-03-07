from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import time
import traceback

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Dict, TypeVar

from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket as ServerWebSocket
from gpt_researcher.actions import stream_output
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.config.config import Config, Settings
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.utils.enum import ReportType, Tone
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.utils.schemas import LogHandler
from pydantic import BaseModel

from backend.server.websocket_manager import WebSocketManager

logger: logging.Logger = get_formatted_logger("gpt_researcher")


class ConfigRequest(BaseModel):
    """Configuration request model.

    This model is used to receive configuration data from the client.
    It should match the structure of the Config class.
    """

    research: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}

    def dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary.

        This method is used to convert the model to a dictionary
        that can be passed to Config.from_dict().
        """
        # Combine research and settings into a single dictionary
        result = {}
        result.update(self.research)
        result.update(self.settings)
        return result


class CustomLogsHandler(LogHandler):
    """Custom handler to capture streaming logs from the research process."""

    def __init__(
        self,
        websocket: ServerWebSocket | None = None,
        task: str | None = None,
    ):
        self.logs: list[dict[str, Any]] = []
        self.websocket: ServerWebSocket | None = websocket
        sanitized_filename: str = sanitize_filename(f"task_{int(time.time())}_{task}")
        self.log_file: Path = Path(os.path.expandvars(os.path.join("outputs", f"{sanitized_filename}.json"))).absolute()
        self.timestamp: str = datetime.now().isoformat()

        # Initialize log file with metadata
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
            report_type=self.report_type,
            websocket=self.logs_handler,
            config=Config(REPORT_TYPE=self.report_type) if config is None else config,
        )

    async def research(self) -> dict[str, Any]:
        """Conduct research and return paths to generated files."""
        await self.researcher.conduct_research()
        report: str = await self.researcher.write_report()

        timestamp: str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        sanitized_filename: str = sanitize_filename(f"task_{timestamp}_{self.query}")
        file_paths: dict[str, str] = await generate_report_files(report, sanitized_filename)

        # Get the JSON log path that was created by CustomLogsHandler
        json_relative_path: str = (
            sanitized_filename if self.logs_handler is None else os.path.relpath(self.logs_handler.log_file)
        )

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
    logs_handler = CustomLogsHandler(websocket=websocket, task=task)
    # Initialize log content with query
    await logs_handler.send_json(
        {
            "query": task,
            "sources": [],
            "context": [],
            "report": "",
        }
    )

    timestamp: str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sanitized_filename: str = sanitize_filename(f"task_{timestamp}_{str(task or '').strip().replace(' ', '_')}")

    report: str = await manager.start_streaming(
        task=str(task or "").strip(),
        report_type=str(report_type or "").strip(),
        report_source=str(report_source or "").strip(),
        source_urls=(source_urls or [])
        if isinstance(source_urls, list)
        else []
        if source_urls is None
        else source_urls.split(","),
        document_urls=(document_urls or [])
        if isinstance(document_urls, list)
        else []
        if document_urls is None
        else document_urls.split(","),
        tone=tone or Tone.Objective,
        websocket=websocket,
        headers=(headers or {}) if isinstance(headers, dict) else json.loads(headers or "{}"),
        query_domains=(query_domains or [])
        if isinstance(query_domains, list)
        else []
        if query_domains is None
        else query_domains.split(","),
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


async def handle_chat(websocket: ServerWebSocket, data: str, manager: WebSocketManager):
    json_data: dict[str, Any] = json.loads(data[4:])
    print(f"Received chat message: {json_data.get('message')}")
    await manager.chat(json_data.get("message", ""), websocket)


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


async def send_file_paths(websocket: ServerWebSocket, file_paths: dict[str, Any]):
    """Send file paths to the frontend.
    
    This function ensures file paths are properly JSON serialized before sending.
    """
    try:
        # Convert file paths to a properly serialized JSON string
        file_paths_json = json.dumps(file_paths)
        await websocket.send_json({"type": "path", "output": file_paths_json})
        logger.info(f"Sent file paths to frontend: {file_paths}")
    except Exception as e:
        logger.exception(f"Error sending file paths: {e}")
        # Fallback attempt - direct serialization
        await websocket.send_json({"type": "path", "output": file_paths})


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
        os.environ[key] = value


async def handle_file_upload(file, DOC_PATH: str) -> dict[str, str]:
    file_path = os.path.join(DOC_PATH, os.path.basename(file.filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    logger.info(f"File uploaded to {file_path}")

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


T = TypeVar("T")


async def handle_websocket_communication(
    websocket: ServerWebSocket,
    manager: WebSocketManager,
) -> None:
    running_task: asyncio.Task | None = None

    def run_long_running_task(
        awaitable: Awaitable[T],
    ) -> asyncio.Task[T | None]:
        async def safe_run() -> T | None:
            try:
                return await awaitable
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
                elif data.startswith("config"):
                    # Handle configuration commands
                    json_data: dict[str, Any] = json.loads(data[7:])
                    command, config_data = extract_config_command_data(json_data)

                    logger.info(f"Received configuration command: {command}")

                    if command == "get":
                        logger.info("Getting current configuration")
                        config_response: JSONResponse = await handle_get_config()
                        config_json: dict[str, Any] = json.loads(config_response.body)
                        await websocket.send_json({"type": "config", "data": config_json})
                        logger.info("Sent current configuration to client")
                    elif command == "save":
                        logger.info("Saving configuration")
                        try:
                            # Create ConfigRequest object from data
                            config_obj = ConfigRequest(**config_data)
                            result: JSONResponse = await handle_save_config(config_obj)
                            success = result.status_code == 200
                            await websocket.send_json({"type": "config_saved", "success": success})
                            logger.info(f"Configuration save {'succeeded' if success else 'failed'}")
                        except Exception as e:
                            logger.exception(f"Error saving configuration: {e.__class__.__name__}: {e}")
                            await websocket.send_json(
                                {"type": "config_saved", "success": False, "error": f"{e.__class__.__name__}: {e}"}
                            )
                    elif command == "default":
                        logger.info("Getting default configuration")
                        config_response = await handle_get_default_config()
                        config_json = json.loads(config_response.body)
                        await websocket.send_json({"type": "default_config", "data": config_json})
                        logger.info("Sent default configuration to client")
                    elif command == "load":
                        # Handle loading a configuration from a file
                        logger.info("Loading configuration from file")
                        if isinstance(config_data, dict):
                            try:
                                # Create ConfigRequest object from data
                                config_obj = ConfigRequest(**config_data)
                                result: JSONResponse = await handle_save_config(config_obj)
                                success = result.status_code == 200
                            except Exception as e:
                                logger.exception(f"Error loading configuration: {e.__class__.__name__}: {e}")
                                await websocket.send_json(
                                    {"type": "config_loaded", "success": False, "error": f"{e.__class__.__name__}: {e}"}
                                )
                            else:
                                await websocket.send_json({"type": "config_loaded", "success": success})
                                logger.info(f"Configuration load {'succeeded' if success else 'failed'}")
                        else:
                            logger.error("Invalid configuration data format")
                            await websocket.send_json(
                                {"type": "config_loaded", "success": False, "error": "Invalid configuration data format"}
                            )
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
    """Extract command data from JSON data."""
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


def extract_config_command_data(
    json_data: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Extract configuration command data from JSON data."""
    return json_data.get("command", ""), json_data.get("data", {})


# Configuration management functions


async def handle_get_config() -> JSONResponse:
    """Handle get configuration request."""
    try:
        logger.info("Getting current configuration")
        config: Config = Config()
        if os.path.exists(Config.DEFAULT_PATH):
            logger.info(f"Loading user configuration from {Config.DEFAULT_PATH}")
            config = Config.from_path(Config.DEFAULT_PATH)
        else:
            logger.info("No configuration found, creating default configuration")
            Config.DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
            Config.DEFAULT_PATH.write_text(config.to_json())
            logger.info(f"Default configuration available at '{Config.DEFAULT_PATH}'")

        config_json: dict[str, Any] = json.loads(config.to_json())

    except Exception as e:
        logger.exception(f"Error getting configuration! {e.__class__.__name__}: {e}")
        return JSONResponse(
            content={"message": f"Error getting configuration! {e.__class__.__name__}: {e}"}, status_code=500
        )

    else:
        logger.info(f"User configuration loaded successfully with {len(config_json)} top-level keys")
        return JSONResponse(content=config_json, status_code=200)


async def handle_save_config(config_request: ConfigRequest) -> JSONResponse:
    """Handle save configuration request."""
    try:
        logger.info("Saving configuration")
        os.makedirs(Config.DEFAULT_PATH, exist_ok=True)

        # Convert the request to a dictionary
        config_dict: dict[str, Any] = config_request.dict()
        logger.info(f"Configuration request contains {len(config_dict)} top-level keys: {', '.join(config_dict.keys())}")

        # Create a Config object from the dictionary
        config: Config = Config.from_dict(config_dict)

        # Save config to file
        logger.info(f"Saving configuration to {Config.DEFAULT_PATH}")
        with open(Config.DEFAULT_PATH, "w") as f:
            f.write(config.to_json())

        logger.info("Configuration saved successfully")
        return JSONResponse(content={"message": "Configuration saved successfully"}, status_code=200)
    except Exception as e:
        logger.exception(f"Error saving configuration! {e.__class__.__name__}: {e}")
        return JSONResponse(content={"message": f"Error saving configuration! {e.__class__.__name__}: {e}"}, status_code=500)


async def handle_get_default_config() -> JSONResponse:
    """Handle get default configuration request."""
    try:
        logger.info("Getting default configuration")

        # Create default config
        config = Config()

        # Create config directory if it doesn't exist
        Config.DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Save default config to file if it doesn't exist
        if not Config.DEFAULT_PATH.exists():
            logger.info(f"User configuration file not found, creating at {Config.DEFAULT_PATH}")
            Config.DEFAULT_PATH.write_text(config.to_json())
            logger.info(f"Default configuration created successfully with {len(config.to_dict())} top-level keys")
        config_dict: dict[str, Any] = json.loads(config.to_json())

    except Exception as e:
        logger.exception(f"Error getting default configuration! {e.__class__.__name__}: {e}")
        return JSONResponse(
            content={"message": f"Error getting default configuration! {e.__class__.__name__}: {e}"}, status_code=500
        )
    else:
        return JSONResponse(content=config_dict, status_code=200)


async def handle_get_settings() -> JSONResponse:
    """Handle get settings request."""
    try:
        logger.info("Getting settings")
        settings: Settings = Settings()
        settings_dict: dict[str, Any] = {"settings": settings.to_dict()}
        logger.info(f"Settings loaded successfully with {len(settings_dict['settings'])} keys")
        return JSONResponse(content=settings_dict, status_code=200)
    except Exception as e:
        logger.exception(f"Error getting settings! {e.__class__.__name__}: {e}")
        return JSONResponse(content={"message": f"Error getting settings! {e.__class__.__name__}: {e}"}, status_code=500)
