from __future__ import annotations

import asyncio
import errno
import json
import logging
import os
import time

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, ClassVar, Dict

from anthropic import BaseModel
from fastapi import FastAPI, File, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from gpt_researcher.config.config import Config
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.utils.logging_config import setup_research_logging

from backend.chat import ChatAgentWithMemory
from backend.server.server_utils import (
    ConfigRequest,
    execute_multi_agents,
    generate_report_files,
    handle_file_deletion,
    handle_file_upload,
    handle_get_config,
    handle_get_settings,
    handle_save_config,
    handle_websocket_communication,
    sanitize_filename,
)
from backend.server.websocket_manager import WebSocketManager


# Get logger instance
logger: logging.Logger = get_formatted_logger(__name__)

# Don't override parent logger settings
logger.propagate = True

# Models


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str


# App initialization
app = FastAPI()


# Ensure outputs directory exists
os.makedirs("outputs", exist_ok=True)

# Static files and templates
app.mount("/site", StaticFiles(directory="./frontend"), name="site")
app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
templates = Jinja2Templates(directory="./frontend")


# Add a specific route for file downloads
@app.get("/outputs/{file_path:path}")
async def download_file(file_path: str) -> FileResponse:
    file_location = f"outputs/{file_path}"
    logger.info(f"Attempting to serve file: {file_location}")
    if os.path.exists(file_location):
        logger.info(f"File found, serving: {file_location}")
        return FileResponse(
            path=file_location,
            filename=os.path.basename(file_location)
        )
    logger.error(f"File not found: {file_location}")
    files_in_dir = os.listdir("outputs")
    logger.error(f"Files in outputs directory: {files_in_dir}")
    return JSONResponse(
        {"detail": f"File not found: {file_location}. Available files: {files_in_dir}"},
        status_code=404,
    )


# WebSocket manager
manager = WebSocketManager()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for compatibility with my_frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
DOC_PATH: str = os.getenv("DOC_PATH", "./my-docs")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Startup Event."""
    os.makedirs("outputs", exist_ok=True)
    os.makedirs(DOC_PATH, exist_ok=True)

    # Setup research logging
    log_file, json_file, research_logger, json_handler = setup_research_logging()
    research_logger.json_handler = json_handler  # type: ignore[attr-value]
    research_logger.info(f"Research log file: {log_file}")
    research_logger.info(f"Research JSON file: {json_file}")

    yield


# Routes


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "report": None})


@app.get("/files/")
async def list_files() -> dict[str, list[str]]:
    files: list[str] = os.listdir(DOC_PATH)
    logger.debug(f"Files in {DOC_PATH}: {files}")
    return {"files": files}


@app.post("/api/multi_agents")
async def run_multi_agents() -> JSONResponse:
    return await execute_multi_agents(manager)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:  # noqa: B008
    return await handle_file_upload(file, DOC_PATH)


@app.delete("/files/{filename}")
async def delete_file(filename: str) -> JSONResponse:
    return await handle_file_deletion(filename, DOC_PATH)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await handle_websocket_communication(websocket, manager)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.exception(f"Error in websocket communication: {e.__class__.__name__}: {e}")
        await manager.disconnect(websocket)


# region New Endpoints
@app.get("/get_config")
async def get_config() -> Dict[str, Any]:
    """Get the current configuration.

    This endpoint is used by my_frontend.
    """
    config_response: JSONResponse = await handle_get_config()
    return json.loads(config_response.body)


@app.post("/save_config")
async def save_config(params: Dict[str, Any]) -> Dict[str, Any]:
    """Save the configuration.

    This endpoint is used by my_frontend.
    """
    try:
        config_obj: ConfigRequest = ConfigRequest(**params)
        result: JSONResponse = await handle_save_config(config_obj)
        return json.loads(result.body)
    except Exception as e:
        logger.exception(f"Error handling save_config request: {e.__class__.__name__}: {e}")
        return {"status": "error", "message": f"Error handling save_config request: {e.__class__.__name__}: {e}"}


@app.get("/get_settings")
async def get_settings() -> Dict[str, Any]:
    """Get the current settings.

    This endpoint is used by my_frontend.
    """
    try:
        settings_response: JSONResponse = await handle_get_settings()
        return json.loads(settings_response.body)
    except Exception as e:
        logger.exception(f"Error handling get_settings request: {e.__class__.__name__}: {e}")
        return {"error": f"Error handling get_settings request: {e.__class__.__name__}: {e}"}


@app.post("/save_settings")
async def save_settings(settings_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save the settings.

    This endpoint is used by my_frontend.
    """
    try:
        settings_path: Path = Path("settings.json")
        settings_path.write_text(json.dumps(settings_data, indent=2))

        if "settings" in settings_data:
            for key, value in settings_data["settings"].items():
                if key == "openai_api_key":
                    os.environ["OPENAI_API_KEY"] = str(value)
                elif key == "tavily_api_key":
                    os.environ["TAVILY_API_KEY"] = str(value)
                elif key == "langchain_api_key":
                    os.environ["LANGCHAIN_API_KEY"] = str(value)
                elif key == "anthropic_api_key":
                    os.environ["ANTHROPIC_API_KEY"] = str(value)
                elif key == "google_api_key":
                    os.environ["GOOGLE_API_KEY"] = str(value)
                elif key == "google_cx_key":
                    os.environ["GOOGLE_CX_KEY"] = str(value)
                elif key == "bing_api_key":
                    os.environ["BING_API_KEY"] = str(value)
                elif key == "searchapi_api_key":
                    os.environ["SEARCHAPI_API_KEY"] = str(value)
                elif key == "serpapi_api_key":
                    os.environ["SERPAPI_API_KEY"] = str(value)
                elif key == "serper_api_key":
                    os.environ["SERPER_API_KEY"] = str(value)
                elif key == "searx_url":
                    os.environ["SEARX_URL"] = str(value)
                elif key == "langchain_tracing_v2":
                    os.environ["LANGCHAIN_TRACING_V2"] = str(value)
                elif key == "retriever":
                    os.environ["RETRIEVER"] = str(value)

        return {"status": "success"}
    except Exception as e:
        logger.exception(f"Error handling save_settings request: {e.__class__.__name__}: {e}")
        return {"status": "error", "message": f"Error handling save_settings request: {e.__class__.__name__}: {e}"}


# endregion


class FrontendLogHandler(logging.Handler):
    def __init__(
        self,
        websocket: WebSocket | None = None,
        message_queue: asyncio.Queue[str] | None = None,
    ) -> None:
        super().__init__()
        self.message_queue: asyncio.Queue[str] | None = message_queue
        self.formatter: logging.Formatter = logging.Formatter("%(levelname)s(%(name)s): %(message)s")
        self.websocket: WebSocket | None = websocket

    def set_message_queue(
        self,
        message_queue: asyncio.Queue[str] | None,
    ) -> None:
        self.message_queue = message_queue

    def emit(
        self,
        record: logging.LogRecord,
    ) -> None:
        no_frontend: bool = getattr(record, "noFrontend", False)
        if not self.message_queue and not no_frontend:
            return
        msg: str = self.format(record)
        if record.exc_info is not None:
            import traceback

            msg = f"{msg}\n{traceback.format_exception(*record.exc_info)}"
        elif record.exc_text and record.exc_text.strip():
            msg = f"{msg}\n{record.exc_text}"
        if no_frontend:
            return
        log_event: dict[str, str] = {"type": "log", "level": record.levelname.lower(), "message": msg}
        if self.message_queue is not None:
            frontend_task: asyncio.Task[None] = asyncio.create_task(self.message_queue.put(json.dumps(log_event)))
            frontend_task.add_done_callback(lambda _: None if self.websocket is None else self.websocket.close())
        if self.websocket is not None:
            frontend_task: asyncio.Task[None] = asyncio.create_task(self.websocket.send_text(json.dumps(log_event)))
            frontend_task.add_done_callback(lambda _: None if self.websocket is None else self.websocket.close())


class ResearchAPIHandler:
    _latest_report: ClassVar[str] = ""
    _chat_agent: ClassVar[ChatAgentWithMemory | None] = None

    @classmethod
    def set_latest_report(
        cls,
        report: str,
        config_path: str = "default",
    ) -> None:
        cls._latest_report = report
        cls._chat_agent = ChatAgentWithMemory(report, config_path, headers={})
        logger.debug("Chat agent initialized with new report")

    @classmethod
    async def process_chat_message(
        cls,
        message: str,
    ) -> str:
        try:
            if not cls._chat_agent or not cls._latest_report:
                return json.dumps(
                    {"type": "chat", "content": "Knowledge empty, please run the research first to obtain knowledge"}
                )
            response: str = await cls._chat_agent.chat(message)
            return json.dumps({"type": "chat", "content": response})
        except Exception as e:
            logger.exception(f"Error in chat process! {e.__class__.__name__}: {e}")
            return json.dumps({"type": "error", "content": f"Error in chat process! {e.__class__.__name__}: {e}"})

    @staticmethod
    async def stream_research(
        params: dict[str, Any],
        websocket: WebSocket,
        websocket_manager: WebSocketManager,
    ) -> AsyncGenerator[str, None]:
        os.environ["LITELLM_LOG"] = "INFO"
        try:
            task: str = params["query"]
            report_type: str = params.get("report_type", "")
            source_urls: list[str] = str(params.get("source_urls", "")).split(",") if params.get("source_urls") else []
            query_domains: list[str] = str(params.get("query_domains", "")).split(",") if params.get("query_domains") else []  # noqa: E501
            document_urls: list[str] = str(params.get("document_urls", "")).split(",") if params.get("document_urls") else []  # noqa: E501
            script_dir = Path(__file__).parent.absolute()
            config_path: Path | None = script_dir / "config.json"
            if config_path and not config_path.is_file():
                try:
                    raise OSError(errno.EISDIR, f"Config file '{config_path}' is not a file!", config_path)
                except Exception as e:
                    logger.exception(f"Config file '{config_path}' is not a file!", exc_info=e)
                config_path = None
            if config_path and config_path.exists():
                logger.info(f"Using config from '{config_path}'")
                config: Config = Config.from_path(config_path)
                config = Config.from_dict(params, config)
            else:
                logger.info("No config file found, using default config")
                config = Config.from_dict(params)
                if config_path is not None:
                    config_path.write_text(config.to_json())
                    logger.info(f"Default config saved to '{config_path}'")
            for dir_path in ["logs", "outputs"]:
                (script_dir / dir_path).mkdir(exist_ok=True, parents=True)
            report: str = await websocket_manager.start_streaming(
                task=task,
                report_type=report_type,
                report_source=config.REPORT_SOURCE.value,
                source_urls=source_urls,
                document_urls=document_urls,
                tone=config.TONE,
                websocket=websocket,
                query_domains=query_domains,
            )
            ResearchAPIHandler.set_latest_report(report, str(config_path))
            yield json.dumps({"type": "report", "output": report})
            sanitized_filename: str = sanitize_filename(f"task_{int(time.time())}_{task}")
            if websocket is not None:
                report: str = await websocket_manager.start_streaming(
                    task=task,
                    report_type=config.REPORT_TYPE.value,
                    report_source=config.REPORT_SOURCE.value,
                    source_urls=source_urls,
                    document_urls=document_urls,
                    tone=config.TONE,
                    websocket=websocket,
                    headers={},
                    query_domains=query_domains,
                )
                report = str(report)
            file_paths: dict[str, str] = await generate_report_files(report, sanitized_filename)
            file_paths["json"] = str(f"logs/{sanitized_filename}.log")
            yield json.dumps({"type": "path", "output": {k: str(f) for k, f in file_paths.items()}})
        except Exception as e:
            logger.exception(f"Error in research process! {e.__class__.__name__}: {e}")
            yield json.dumps({"type": "error", "output": f"Error in research process! {e.__class__.__name__}: {e}"})


@app.websocket("/ws/research")
async def websocket_research(websocket: WebSocket):
    await websocket.accept()
    try:
        data: str = await websocket.receive_text()
        params: dict = json.loads(data)
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "content": f"Invalid parameters: {e}"}))
        await websocket.close()
        return
    websocket_manager = WebSocketManager()
    try:
        async for chunk in ResearchAPIHandler.stream_research(params, websocket, websocket_manager):
            await websocket.send_text(chunk)
        await websocket.close()
    except Exception as e:
        logger.exception(f"Error in research websocket endpoint: {e.__class__.__name__}: {e}")
        await websocket.send_text(
            json.dumps({"type": "error", "output": f"Error in research process! {e.__class__.__name__}: {e}"})
        )
        await websocket.close()


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message: str = await websocket.receive_text()
            response: str = await ResearchAPIHandler.process_chat_message(message)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        logger.info("WebSocket chat disconnected")


# endregion
