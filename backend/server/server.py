from __future__ import annotations

import logging
import os

from typing import TYPE_CHECKING

from fastapi import FastAPI, File, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.utils.logging_config import setup_research_logging
from pydantic import BaseModel

from backend.server.server_utils import (
    execute_multi_agents,
    handle_file_deletion,
    handle_file_upload,
    handle_websocket_communication,
)
from backend.server.websocket_manager import WebSocketManager

if TYPE_CHECKING:
    from fastapi import Request, UploadFile, WebSocket
    from fastapi.responses import JSONResponse

# Get logger instance
logger: logging.Logger = get_formatted_logger(__name__)

# Don't override parent logger settings
logger.propagate = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Only log to console
    ],
)


# Models


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str


class ConfigRequest(BaseModel):
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: str
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_API_KEY: str
    OPENAI_API_KEY: str
    DOC_PATH: str
    RETRIEVER: str
    GOOGLE_API_KEY: str = ""
    GOOGLE_CX_KEY: str = ""
    BING_API_KEY: str = ""
    SEARCHAPI_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    SEARX_URL: str = ""
    XAI_API_KEY: str


# App initialization
app = FastAPI()

# Static files and templates
app.mount("/site", StaticFiles(directory="./frontend"), name="site")
app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")
templates = Jinja2Templates(directory="./frontend")

# WebSocket manager
manager = WebSocketManager()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
DOC_PATH = os.getenv("DOC_PATH", "./my-docs")

# Startup event


@app.on_event("startup")
def startup_event():
    os.makedirs("outputs", exist_ok=True)
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    os.makedirs(DOC_PATH, exist_ok=True)

    # Setup research logging
    log_file, json_file, research_logger, json_handler = setup_research_logging()  # Unpack all 4 values
    research_logger.json_handler = json_handler  # Store the JSON handler on the logger  # pyright: ignore[reportAttributeAccessIssue]
    research_logger.info(f"Research log file: {log_file}")
    research_logger.info(f"Research JSON file: {json_file}")


# Routes


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "report": None})


@app.get("/files/")
async def list_files() -> dict[str, list[str]]:
    files: list[str] = os.listdir(DOC_PATH)
    print(f"Files in {DOC_PATH}: {files}")
    return {"files": files}


@app.post("/api/multi_agents")
async def run_multi_agents() -> JSONResponse:
    return await execute_multi_agents(manager)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
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
