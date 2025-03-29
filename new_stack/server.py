from __future__ import annotations

import argparse
import asyncio
import errno
import json
import logging
import mimetypes
import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, AsyncGenerator, ClassVar

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, Template


try:
    from gpt_researcher.config import Config
except ImportError:
    import sys

    sys.path.append(str(Path(__file__).parents[1]))
    from gpt_researcher.config import Config

from backend.chat import ChatAgentWithMemory
from backend.server.server_utils import generate_report_files, sanitize_filename
from backend.server.websocket_manager import WebSocketManager
from gpt_researcher.config.config import Config
from gpt_researcher.utils.enum import Tone
from gpt_researcher.utils.logger import get_formatted_logger


SCRIPT_DIR: Path = Path(__file__).parent.absolute()

logger: logging.Logger = get_formatted_logger(__name__, SCRIPT_DIR / "logs")

mimetypes.init()
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/html", ".html")


class ResearchAPIHandler:
    """Handler for research API requests."""

    _latest_report: ClassVar[str] = ""
    _chat_agent: ClassVar[ChatAgentWithMemory | None] = None

    @classmethod
    def set_latest_report(
        cls,
        report: str,
        config_path: str = "default",
    ) -> None:
        """Set the latest report and initialize a chat agent for it."""
        cls._latest_report = report
        cls._chat_agent = ChatAgentWithMemory(report, config_path, headers={})
        logger.debug("Chat agent initialized with new report")

    @classmethod
    async def process_chat_message(
        cls,
        message: str,
    ) -> str:
        """Process a chat message and return the response as a JSON string.

        Uses ChatAgentWithMemory directly instead of WebSocketManager
        to align with the Next.js implementation.
        """
        try:
            if not cls._chat_agent or not cls._latest_report:
                return json.dumps(
                    {
                        "type": "chat",
                        "content": "Knowledge empty, please run the research first to obtain knowledge",
                    }
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
        """Stream the research process with progress updates."""
        os.environ["LITELLM_LOG"] = "INFO"
        try:
            task: str = params["query"]
            report_type: str = params.get("report_type", "")
            source_urls: list[str] = str(params.get("source_urls", "")).split(",") if params.get("source_urls") else []
            query_domains: list[str] = (
                str(params.get("query_domains", "")).split(",") if params.get("query_domains") else []
            )
            config_path: Path | None = SCRIPT_DIR / "config.json"
            if config_path and not config_path.is_file():
                try:
                    raise OSError(
                        errno.EISDIR,
                        f"Config file '{config_path}' is not a file! {os.strerror(errno.EISDIR)}",
                        config_path,
                    )
                except Exception as e:
                    logger.exception(
                        f"Config file '{config_path}' is not a file!",
                        exc_info=e,
                    )
                config_path = None

            if config_path and config_path.exists():
                logger.info(f"Using config from '{config_path}'")
                config = Config.from_dict(params, Config.from_path(config_path))
            else:
                logger.info("No config file found, using default config")
                config = Config.from_dict(params)
                if config_path is not None:
                    config_path.write_text(config.to_json())
                    logger.info(f"Default config saved to '{config_path}'")

            for dir_path in ["logs", "outputs"]:
                (SCRIPT_DIR / dir_path).mkdir(exist_ok=True, parents=True)

            report: str = await websocket_manager.start_streaming(
                task=task,
                report_type=report_type,
                report_source=config.REPORT_SOURCE.value,
                source_urls=source_urls,
                document_urls=[],
                tone=config.TONE,
                websocket=websocket,
                query_domains=query_domains,
            )

            ResearchAPIHandler.set_latest_report(report, str(config_path))
            yield json.dumps({"type": "report", "output": report})

            sanitized_filename: str = sanitize_filename(f"task_{int(time.time())}_{task}")
            file_paths: dict[str, str] = await generate_report_files(report, sanitized_filename)

            # Convert backslashes to forward slashes and ensure proper URL paths
            file_paths = {k: f"/file/{str(f).replace('\\', '/')}" for k, f in file_paths.items()}
            file_paths["json"] = f"/file/logs/{sanitized_filename}.log"
            yield json.dumps({"type": "path", "output": file_paths})

        except Exception as e:
            logger.exception(f"Error in research process! {e.__class__.__name__}: {e}")
            yield json.dumps({"type": "error", "output": f"Error in research process! {e.__class__.__name__}: {e}"})


env = Environment(loader=FileSystemLoader(SCRIPT_DIR / "static/templates"), autoescape=True)


class FrontendLogHandler(logging.Handler):
    """Custom logging handler that sends logs to the frontend via a message queue or websocket."""

    def __init__(
        self,
        websocket: WebSocket | None = None,
        message_queue: asyncio.Queue[str] | None = None,
    ) -> None:
        super().__init__()
        self.message_queue: asyncio.Queue[str] | None = message_queue
        self.formatter: logging.Formatter = logging.Formatter("%(levelname)s(%(name)s): %(message)s")
        self.websocket: WebSocket | None = websocket

    def set_message_queue(self, message_queue: asyncio.Queue[str] | None) -> None:
        """Set the message queue to use for sending logs."""
        self.message_queue = message_queue

    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to the frontend."""
        no_frontend: bool = getattr(record, "noFrontend", False)

        if not self.message_queue and not no_frontend:
            return

        msg: str = self.formatter.format(record)
        if record.exc_info is not None:
            import traceback

            msg = f"{msg}\n{traceback.format_exception(*record.exc_info)}"
        elif record.exc_text and record.exc_text.strip():
            msg = f"{msg}\n{record.exc_text}"

        if no_frontend:
            return

        log_event: dict[str, str] = {"type": "log", "level": record.levelname.lower(), "message": msg}

        if self.message_queue is not None:
            log_task: asyncio.Task[None] = asyncio.create_task(self.message_queue.put(json.dumps(log_event)))
            log_task.add_done_callback(lambda _: logger.debug(f"Log event put into message queue: {log_event}"))
        if self.websocket is not None:
            log_task: asyncio.Task[None] = asyncio.create_task(self.websocket.send_text(json.dumps(log_event)))
            log_task.add_done_callback(lambda _: logger.debug(f"Log event sent to websocket: {log_event}"))


log_handler = FrontendLogHandler()
logger.addHandler(log_handler)

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(SCRIPT_DIR / "static")), name="static")
app.mount("/outputs", StaticFiles(directory=str(SCRIPT_DIR / "outputs")), name="outputs")
executor = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())


@app.get("/file/{filename:path}")
async def serve_file(filename: str):
    """Serve files from the outputs directory with proper content type."""
    file_path = SCRIPT_DIR / "outputs" / filename
    if not file_path.is_file():
        return JSONResponse(status_code=404, content={"detail": "File not found"})
    return FileResponse(str(file_path))


def configure_frontend(frontend_path: str) -> None:
    """Configure the frontend path for the application."""
    global app
    try:
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
        logger.info(f"Frontend configured with path: {frontend_path}")
    except Exception as e:
        logger.error(f"Failed to configure frontend: {e}")


@app.get("/", response_class=HTMLResponse)
async def read_index() -> HTMLResponse:
    try:
        config_path: Path = SCRIPT_DIR / "config.json"
        if config_path.exists():
            config: Config = Config.from_path(config_path)
        else:
            config = Config()

        # Create a dictionary-like wrapper for the Config object
        class ConfigWrapper:
            def __init__(self, config_obj):
                self.config = config_obj

            def get(self, key, default=""):
                # Try to get the attribute from the Config object
                return getattr(self.config, key, default)

            def __getattr__(self, name):
                # Forward attribute access to the Config object
                return getattr(self.config, name)

        # Wrap the Config object
        config_wrapper = ConfigWrapper(config)

        # Get settings from settings.json if it exists
        settings_path: Path = SCRIPT_DIR / "settings.json"
        settings = {}
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
                if "settings" in settings:
                    settings = settings["settings"]
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")

        context: dict[str, Any] = {
            "config": config_wrapper,
            "settings": settings,
            "report_types": {
                "ResearchReport": "Quick Summary (~2 min)",
                "ResourceReport": "Resource Report",
                "DetailedReport": "Detailed Analysis (~5 min)",
                "MultiAgents": "Multi-Agent Report",
            },
            "report_sources": {
                "web": "Web Sources",
                "local": "Local Documents",
                "all": "All Sources",
            },
            "report_formats": {
                "APA": "APA",
                "MLA": "MLA",
                "CHICAGO": "Chicago",
                "HARVARD": "Harvard",
                "IEEE": "IEEE",
            },
            "output_formats": {
                "MARKDOWN": "Markdown",
                "PDF": "PDF",
                "DOCX": "Word Document",
                "TXT": "Plain Text",
            },
            "retrievers": {
                "tavily": "Tavily",
                "google": "Google",
                "bing": "Bing",
                "searchapi": "SearchAPI",
                "serpapi": "SerpAPI",
                "serper": "Serper",
                "searx": "SearX",
            },
            "tones": {
                "Objective": Tone.Objective.value,
                "Formal": Tone.Formal.value,
                "Analytical": Tone.Analytical.value,
                "Persuasive": Tone.Persuasive.value,
                "Informative": Tone.Informative.value,
                "Explanatory": Tone.Explanatory.value,
                "Descriptive": Tone.Descriptive.value,
                "Critical": Tone.Critical.value,
                "Comparative": Tone.Comparative.value,
                "Speculative": Tone.Speculative.value,
                "Reflective": Tone.Reflective.value,
                "Narrative": Tone.Narrative.value,
                "Humorous": Tone.Humorous.value,
                "Optimistic": Tone.Optimistic.value,
                "Pessimistic": Tone.Pessimistic.value,
            },
            "api_keys": {
                "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", ""),
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                "LANGCHAIN_API_KEY": os.environ.get("LANGCHAIN_API_KEY", ""),
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
                "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
                "GOOGLE_CX_KEY": os.environ.get("GOOGLE_CX_KEY", ""),
                "BING_API_KEY": os.environ.get("BING_API_KEY", ""),
                "SEARCHAPI_API_KEY": os.environ.get("SEARCHAPI_API_KEY", ""),
                "SERPAPI_API_KEY": os.environ.get("SERPAPI_API_KEY", ""),
                "SERPER_API_KEY": os.environ.get("SERPER_API_KEY", ""),
                "SEARX_URL": os.environ.get("SEARX_URL", ""),
            },
            "available_configs": Config.list_available_configs(),
        }

        template: Template = env.get_template("index.html")
        html_content: str = template.render(**context)
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.exception(f"Error rendering template in GET request: {e.__class__.__name__}: {e}")
        return HTMLResponse(
            content=f"<html><body><h1>500 Server Error</h1><p>{e.__class__.__name__}: {e}</p></body></html>",
            status_code=500,
        )


@app.get("/get_config")
async def get_config() -> JSONResponse:
    try:
        config_path: Path = SCRIPT_DIR / "config.json"
        if config_path.exists():
            config: Config = Config.from_path(config_path)
            config_dict: dict[str, Any] = config.to_dict()
        else:
            config = Config()
            config_dict = config.to_dict()
        return JSONResponse(content=config_dict, status_code=200)
    except Exception as e:
        logger.exception(f"Error handling get_config request! {e.__class__.__name__}: {e}")
        return JSONResponse(
            content={"error": f"Error handling get_config request! {e.__class__.__name__}: {e}"}, status_code=500
        )


@app.get("/get_settings")
async def get_settings() -> JSONResponse:
    try:
        settings_path: Path = SCRIPT_DIR / "settings.json"
        if settings_path.exists():
            settings_data = json.loads(settings_path.read_text())
        else:
            settings_data: dict[str, dict[str, Any]] = {"settings": {}}
        return JSONResponse(content=settings_data, status_code=200)
    except Exception as e:
        logger.exception(f"Error handling get_settings request! {e.__class__.__name__}: {e}")
        return JSONResponse(
            content={"error": f"Error handling get_settings request! {e.__class__.__name__}: {e}"}, status_code=500
        )


@app.post("/save_config")
async def save_config(request: Request) -> JSONResponse:
    try:
        params: dict[str, Any] = await request.json()
        config_path: Path = SCRIPT_DIR / "config.json"
        config: Config = Config.from_dict(params)
        config_path.write_text(config.to_json())
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logger.exception(f"Error handling save_config request: {e.__class__.__name__}: {e}")
        return JSONResponse(
            content={"error": f"Error handling save_config request! {e.__class__.__name__}: {e}"},
            status_code=500,
        )


@app.post("/save_settings")
async def save_settings(request: Request) -> JSONResponse:
    try:
        settings_data: dict[str, Any] = await request.json()
        settings_path: Path = SCRIPT_DIR / "settings.json"
        settings_path.write_text(json.dumps(settings_data, indent=2))

        if "settings" in settings_data:
            for key, value in dict(settings_data["settings"]).items():
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

        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logger.exception(f"Error handling save_settings request: {e.__class__.__name__}: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.websocket("/ws/research")
async def websocket_research(websocket: WebSocket):
    await websocket.accept()
    try:
        data: str = await websocket.receive_text()
        params: dict[str, Any] = json.loads(data)
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "content": f"Invalid parameters: {e}"}))
        await websocket.close()
        return

    log_handler.websocket = websocket

    try:
        async for chunk in ResearchAPIHandler.stream_research(params, websocket, WebSocketManager()):
            await websocket.send_text(chunk)
        await websocket.close()
    except Exception as e:
        logger.exception(f"Error in research websocket endpoint: {e.__class__.__name__}: {e}")
        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "output": f"Error in research process! {e.__class__.__name__}: {e}",
                }
            )
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


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run the GPT Researcher web server")
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the server on (default: 8080)",
    )
    parser.add_argument("--frontend", type=str, default="legacy")  # "legacy" or "new"
    parser.add_argument("--reload", type=bool, default=True)
    args: argparse.Namespace = parser.parse_args()
    if args.frontend == "legacy":
        configure_frontend("./frontend")
    elif args.frontend == "new":
        configure_frontend("./my_frontend")
    import uvicorn

    uvicorn.run("my_frontend.server:app", host="0.0.0.0", port=args.port, reload=args.reload)
