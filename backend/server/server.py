from __future__ import annotations

import logging
import os

from datetime import datetime
from typing import Any, Awaitable, Callable

from colorama import Style
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
from gpt_researcher.config.config import Config
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
logger: logging.Logger = logging.getLogger(__name__)

# Don't override parent logger settings
logger.propagate = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Only log to console
    ],
)


# Custom middleware to set cache control headers for outputs URLs
class OutputsCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Set cache control headers for outputs URLs.

        Args:
            request (Request): The request object.
            call_next (Callable[[Request], Awaitable[Response]]): The next middleware function.

        Returns:
            Response: The response object.
        """
        config: Config = Config("default")
        cache_expiry: datetime = datetime.now() + config.cache_expiry_time
        response: Response = await call_next(request)

        # Check if this is a request for an output file
        if request.url.path.startswith("/outputs/"):
            # Set Cache-Control header using CACHE_EXPIRY_TIME
            max_age_seconds: int = int(config.cache_expiry_time.total_seconds())
            response.headers["Cache-Control"] = f"public, max-age={max_age_seconds}"
            # Also add other cache headers for better browser compatibility
            response.headers["Expires"] = cache_expiry.strftime("%a, %d %b %Y %H:%M:%S GMT")
            # Use ETag for better caching
            response.headers.setdefault("ETag", f'W/"{hash(request.url.path)}"')

        return response


# Models


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    report_source: str
    tone: str
    headers: dict | None = None
    repo_name: str
    branch_name: str
    generate_in_background: bool = True


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


# Get proxy prefix from environment variable
PROXY_PREFIX = os.getenv("PROXY_PREFIX", "")
if PROXY_PREFIX:
    app = FastAPI(root_path=PROXY_PREFIX)
else:
    app = FastAPI()

# Add the custom middleware for output files caching
app.add_middleware(OutputsCacheMiddleware)

# Static files and templates
app.mount("/site", StaticFiles(directory="./frontend"), name="site")
app.mount("/frontend", StaticFiles(directory="./frontend"), name="frontend")  # Mirror /site for clarity.
app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")
templates = Jinja2Templates(directory="./frontend")

# WebSocket manager
manager = WebSocketManager()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    # os.makedirs(DOC_PATH, exist_ok=True)  # Commented out to avoid creating the folder if not needed


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
    print(f"{Style.BRIGHT}Files in {DOC_PATH}: {files}{Style.RESET_ALL}")
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
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected: {e.__class__.__name__}: {e}")
        print(f"WebSocket disconnected: {e.__class__.__name__}: {e}")
        await manager.disconnect(websocket)
