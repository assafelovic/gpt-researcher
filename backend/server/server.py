from __future__ import annotations

import logging
import os
from typing import Any, Awaitable, Callable

from fastapi import (
    FastAPI,
    File,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from backend.server.server_utils import (
    execute_multi_agents,
    handle_file_deletion,
    handle_file_upload,
    handle_websocket_communication,
)
from backend.server.websocket_manager import WebSocketManager

# Get logger instance
logger = logging.getLogger(__name__)

# Don't override parent logger settings
logger.propagate = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Only log to console
    ]
)

# Custom middleware to set cache control headers for outputs URLs
class OutputsCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response: Response = await call_next(request)

        # Check if this is a request for an output file
        if request.url.path.startswith('/outputs/'):
            # Set Cache-Control header for long-term caching (30 days)
            response.headers['Cache-Control'] = 'public, max-age=2592000'
            # Also add other cache headers for better browser compatibility
            response.headers['Expires'] = '30d'
            # Use ETag for better caching
            response.headers.setdefault('ETag', f'W/"{hash(request.url.path)}"')

        return response

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
    DEEPSEEK_API_KEY: str


# App initialization
app = FastAPI()

# Add the custom middleware for output files caching
app.add_middleware(OutputsCacheMiddleware)

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
DOC_PATH: str = os.getenv("DOC_PATH", "./my-docs")

# Startup event


@app.on_event("startup")
def startup_event():
    os.makedirs("outputs", exist_ok=True)
    # Use the standard StaticFiles mount - our middleware will handle cache control
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    os.makedirs(DOC_PATH, exist_ok=True)


# Routes


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "report": None,
        },
    )


@app.get("/files/")
async def list_files() -> dict[str, list[str]]:
    files: list[str] = os.listdir(DOC_PATH)
    print(f"Files in {DOC_PATH}: {files}")
    return {"files": files}


@app.post("/api/multi_agents")
async def run_multi_agents() -> dict[str, Any]:
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
