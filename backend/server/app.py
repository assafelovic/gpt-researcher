import json
import os
from typing import Dict, List, Any
import time
import logging
import sys
import warnings
import httpx

# Suppress Pydantic V2 migration warnings
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, ConfigDict

# Add the parent directory to sys.path to make sure we can import from server
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.websocket_manager import WebSocketManager
from server.server_utils import (
    get_config_dict, sanitize_filename,
    update_environment_variables, handle_file_upload, handle_file_deletion,
    execute_multi_agents, handle_websocket_communication
)
from server.server_utils import CustomLogsHandler

from server.websocket_manager import run_agent
from utils import write_md_to_word, write_md_to_pdf, write_text_to_md
from gpt_researcher.utils.enum import Tone
from chat.chat import ChatAgentWithMemory

# Output file controls
def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}

# Default behavior: keep markdown for processing and PDF for preview; skip DOCX unless explicitly enabled.
SAVE_MD = _env_bool("OUTPUT_SAVE_MD", True)
SAVE_PDF = _env_bool("OUTPUT_SAVE_PDF", True)
SAVE_DOCX = _env_bool("OUTPUT_SAVE_DOCX", False)

# MongoDB services removed - no database persistence needed

# Setup logging
logger = logging.getLogger(__name__)

# Don't override parent logger settings
logger.propagate = True

# Silence uvicorn reload logs
logging.getLogger("uvicorn.supervisors.ChangeReload").setLevel(logging.WARNING)

# Models


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    report_source: str
    tone: str
    headers: dict | None = None
    user_id: int | None = None  # User ID (can also be in headers)
    research_id: str | None = None # Unique ID for the research request
    language: str | None = None  # Language for the report
    project_id: str | None = None  # Project ID to pass through to webhook
    # Webhook URL is configured via environment variable WEBHOOK_URL, not passed in request


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")  # Allow extra fields in the request
    
    report: str
    messages: List[Dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("outputs", exist_ok=True)
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    
    # Mount frontend static files
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
    if os.path.exists(frontend_path):
        app.mount("/site", StaticFiles(directory=frontend_path), name="frontend")
        logger.debug(f"Frontend mounted from: {frontend_path}")
        
        # Also mount the static directory directly for assets referenced as /static/
        static_path = os.path.join(frontend_path, "static")
        if os.path.exists(static_path):
            app.mount("/static", StaticFiles(directory=static_path), name="static")
            logger.debug(f"Static assets mounted from: {static_path}")
    else:
        logger.warning(f"Frontend directory not found: {frontend_path}")
    
    logger.info("GPT Researcher API ready - local mode (no database persistence)")
    yield
    # Shutdown
    logger.info("Research API shutting down")

# App initialization
app = FastAPI(lifespan=lifespan)

# Configure allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Local development
    "http://127.0.0.1:3000",   # Local development alternative
    "https://app.gptr.dev",    # Production frontend
    "*",                      # Allow all origins for testing
]

# Standard JSON response - no custom MongoDB encoding needed

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use default JSON response class

# Mount static files for frontend
# Get the absolute path to the frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

# Mount static directories
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")
app.mount("/site", StaticFiles(directory=frontend_dir), name="site")

# WebSocket manager
manager = WebSocketManager()

# Constants
DOC_PATH = os.getenv("DOC_PATH", "./my-docs")

# Startup event


# Lifespan events now handled in the lifespan context manager above


# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend HTML page."""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    index_path = os.path.join(frontend_dir, "index.html")
    
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return HTMLResponse(content=content)

@app.get("/report/{research_id}")
async def read_report(request: Request, research_id: str):
    docx_path = os.path.join('outputs', f"{research_id}.docx")
    if not os.path.exists(docx_path):
        return {"message": "Report not found."}
    return FileResponse(docx_path)


# Simplified API routes - no database persistence
@app.get("/api/reports")
async def get_all_reports(report_ids: str = None):
    """Get research reports - returns empty list since no database."""
    logger.debug("No database configured - returning empty reports list")
    return {"reports": []}


@app.get("/api/reports/{research_id}")
async def get_report_by_id(research_id: str):
    """Get a specific research report by ID - no database configured."""
    logger.debug(f"No database configured - cannot retrieve report {research_id}")
    raise HTTPException(status_code=404, detail="Report not found")


@app.post("/api/reports")
async def create_or_update_report(request: Request):
    """Create or update a research report - no database persistence."""
    try:
        data = await request.json()
        research_id = data.get("id", "temp_id")
        logger.debug(f"Report creation requested for ID: {research_id} - no database configured, not persisted")
        return {"success": True, "id": research_id}
    except Exception as e:
        logger.error(f"Error processing report creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def write_report(research_request: ResearchRequest, research_id: str = None, logs_handler: CustomLogsHandler | None = None):
    try:
        # Determine user_id early so we can include it in webhook notifications as well
        user_id: int | None = None
        if hasattr(research_request, "user_id") and research_request.user_id:
            user_id = research_request.user_id
        elif research_request.headers and isinstance(research_request.headers, dict):
            header_user_id = research_request.headers.get("user_id")
            try:
                user_id = int(header_user_id) if header_user_id is not None else None
            except (TypeError, ValueError):
                user_id = None
        
        # Determine project_id
        project_id: str | None = None
        if hasattr(research_request, "project_id") and research_request.project_id:
            project_id = research_request.project_id

        # Inject language into headers if provided
        if hasattr(research_request, "language") and research_request.language:
            if research_request.headers is None:
                research_request.headers = {}
            research_request.headers["LANGUAGE"] = research_request.language

        report_information = await run_agent(
            task=research_request.task,
            report_type=research_request.report_type,
            report_source=research_request.report_source,
            source_urls=[],
            document_urls=[],
            tone=Tone[research_request.tone],
            websocket=logs_handler,
            headers=research_request.headers,
            query_domains=[],
            config_path="",
            return_researcher=True
        )

        md_path = await write_text_to_md(report_information[0], research_id) if SAVE_MD else None
        pdf_path = await write_md_to_pdf(report_information[0], research_id) if SAVE_PDF else None
        docx_path = await write_md_to_word(report_information[0], research_id) if SAVE_DOCX else None
        if research_request.report_type != "multi_agents":
            report, researcher = report_information
            response = {
                "research_id": research_id,
                "user_id": user_id,
                "project_id": project_id,
                "research_information": {
                    "source_urls": researcher.get_source_urls(),
                    "research_costs": researcher.get_costs(),
                    "token_usage": researcher.get_token_usage(),
                    "visited_urls": list(researcher.visited_urls),
                    "research_images": researcher.get_research_images(),
                    # "research_sources": researcher.get_research_sources(),  # Raw content of sources may be very large
                },
                "report": report,
                "md_path": md_path,
                "docx_path": docx_path,
                "pdf_path": pdf_path
            }
        else:
            # Keep schema stable even for multi_agents, since some webhook receivers validate fields strictly
            response = {
                "research_id": research_id,
                "user_id": user_id,
                "project_id": project_id,
                "research_information": {
                    "source_urls": [],
                    "research_costs": 0.0,
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "visited_urls": [],
                    "research_images": [],
                },
                "report": "",
                "md_path": md_path,
                "docx_path": docx_path,
                "pdf_path": pdf_path
            }

        # Persist a final snapshot into outputs/{research_id}.json when invoked via HTTP (/report/)
        if logs_handler is not None:
            try:
                await logs_handler.send_json({
                    "query": research_request.task,
                    "report": response.get("report", ""),
                    "costs": response.get("research_information", {}).get("research_costs", 0.0),
                    "token_usage": response.get("research_information", {}).get("token_usage", {}),
                    "sources": response.get("research_information", {}).get("source_urls", []),
                    "context": [],  # keep as empty to avoid huge dumps; events contain details if streamed
                    "output": {
                        "md": response.get("md_path") or "",
                        "pdf": response.get("pdf_path") or "",
                        "docx": response.get("docx_path") or "",
                        "json": logs_handler.log_file,
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to write final JSON log snapshot: {e}")

        # Send webhook notification (if configured in environment)
        await send_webhook_notification(
            research_id=research_id,
            user_id=user_id,
            project_id=project_id,
            status="completed",
            response=response
        )

        return response
    except Exception as e:
        # Send error webhook (if configured in environment)
        await send_webhook_notification(
            research_id=research_id,
            user_id=research_request.user_id if hasattr(research_request, "user_id") else None,
            project_id=research_request.project_id if hasattr(research_request, "project_id") else None,
            status="failed",
            error=str(e)
        )
        raise


async def send_webhook_notification(
    research_id: str,
    user_id: int | None,
    project_id: str | None,
    status: str,
    response: Dict[str, Any] = None,
    error: str = None
):
    """
    Send webhook notification when report generation is complete or failed.
    
    Webhook URL and API key are read from environment variables:
    - WEBHOOK_URL: The webhook URL to send notification to
    - WEBHOOK_API_KEY: The API key for authentication (optional)
    
    If WEBHOOK_URL is not configured, this function does nothing.
    
    Args:
        research_id: The research ID
        status: "completed" or "failed"
        response: The response data (if completed)
        error: Error message (if failed)
    """
    # Get webhook URL from environment variable
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        # Webhook not configured, skip notification
        return
    
    try:
        # Normalize timestamps and payload types to satisfy strict webhook schemas
        timestamp = int(time.time())

        payload = {
            "research_id": research_id,
            "research_id": research_id,
            "user_id": user_id,
            "project_id": project_id,
            "status": status,
            "timestamp": timestamp
        }
        
        if status == "completed" and response:
            research_information = response.get("research_information") or {}
            if not isinstance(research_information, dict):
                research_information = {}
            # Ensure commonly validated keys exist to avoid 400 from strict webhook receivers
            research_information.setdefault("research_costs", 0.0)
            research_information.setdefault(
                "token_usage",
                {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            )
            research_information.setdefault("source_urls", [])
            research_information.setdefault("visited_urls", [])
            research_information.setdefault("research_images", [])

            # Ensure token_usage is shaped correctly
            token_usage = research_information.get("token_usage")
            if not isinstance(token_usage, dict):
                token_usage = {}
            token_usage.setdefault("prompt_tokens", 0)
            token_usage.setdefault("completion_tokens", 0)
            token_usage.setdefault(
                "total_tokens",
                token_usage.get("prompt_tokens", 0) + token_usage.get("completion_tokens", 0),
            )
            research_information["token_usage"] = token_usage

            # Ensure research_costs is numeric
            try:
                research_information["research_costs"] = float(research_information.get("research_costs", 0.0))
            except (TypeError, ValueError):
                research_information["research_costs"] = 0.0

            payload["data"] = {
                "report": response.get("report", ""),
                # Keep paths as strings (some receivers reject null)
                "md_path": response.get("md_path") or "",
                "docx_path": response.get("docx_path") or "",
                "pdf_path": response.get("pdf_path") or "",
                "research_information": research_information
            }
        elif status == "failed" and error:
            # Some receivers validate `data.research_information` even for failures.
            payload["error"] = error
            payload["data"] = {
                "report": "",
                "md_path": "",
                "docx_path": "",
                "pdf_path": "",
                "research_information": {
                    "research_costs": 0.0,
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "source_urls": [],
                    "visited_urls": [],
                    "research_images": [],
                },
            }

        # Log payload (redact markdown report content to avoid huge logs)
        try:
            log_payload = json.loads(json.dumps(payload))  # deep copy via json-serialize (payload is json-safe)
            data = log_payload.get("data")
            if isinstance(data, dict) and "report" in data:
                report_text = data.get("report") or ""
                if not isinstance(report_text, str):
                    report_text = str(report_text)
                preview_len = 240
                data["report"] = report_text[:preview_len]
                data["report_preview_len"] = min(len(report_text), preview_len)
                data["report_total_len"] = len(report_text)
            logger.info(f"Webhook outgoing payload (report truncated): {json.dumps(log_payload, ensure_ascii=False)}")
        except Exception as e:
            logger.warning(f"Failed to log webhook payload preview: {e}")
        
        # Prepare request headers with API key if configured
        headers = {}
        webhook_api_key = os.getenv("WEBHOOK_API_KEY")
        if webhook_api_key:
            headers["x-api-key"] = webhook_api_key
        # Some webhook receivers enforce host allow-lists and may reject `host.docker.internal`.
        # Allow overriding the Host header for compatibility (e.g. set to "localhost:8081").
        webhook_host_header = os.getenv("WEBHOOK_HOST_HEADER")
        if webhook_host_header:
            headers["Host"] = webhook_host_header
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            result = await client.post(webhook_url, json=payload, headers=headers)
            try:
                result.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Log receiver response body for fast debugging (especially on 400)
                resp_text = ""
                try:
                    resp_text = e.response.text
                except Exception:
                    resp_text = "<unable to read response body>"
                logger.error(
                    f"Webhook receiver returned {e.response.status_code} for research_id={research_id}. "
                    f"Response body: {resp_text}"
                )
                raise
            logger.info(f"Webhook notification sent successfully to {webhook_url} for research_id: {research_id}")
    except Exception as e:
        logger.error(f"Failed to send webhook notification to {webhook_url}: {e}")

@app.post("/report/")
async def generate_report(
    research_request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a report generation task.
    
    This endpoint immediately returns a task_id and processes the report in the background.
    When complete, a webhook notification will be sent if WEBHOOK_URL is configured in environment.
    """
    from server.server_utils import sanitize_filename
    import re
    
    if research_request.research_id:
        # Basic sanitization for custom ID: allow alphanumeric, underscores, and dashes
        research_id = re.sub(r"[^a-zA-Z0-9_\-]", "", research_request.research_id)
        if not research_id:
            # Fallback if sanitization results in empty string
            research_id = sanitize_filename(f"task_{int(time.time())}_{research_request.task}")
    else:
        research_id = sanitize_filename(f"task_{int(time.time())}_{research_request.task}")

    # Create per-request JSON log file (even for HTTP /report/ calls)
    logs_handler = CustomLogsHandler(None, research_request.task, sanitized_filename=research_id)
    # Seed basic metadata
    try:
        await logs_handler.send_json({"query": research_request.task})
    except Exception as e:
        logger.warning(f"Failed to initialize JSON log file: {e}")
    
    # Prepare headers
    headers = research_request.headers or {}
    
    # Ensure user_id is in headers if provided in request
    if hasattr(research_request, 'user_id') and research_request.user_id:
        headers["user_id"] = research_request.user_id
    
    # If no retriever specified, use default from environment or config
    if "retriever" not in headers and "retrievers" not in headers:
        # Check environment variable first
        default_retrievers = os.getenv("DEFAULT_RETRIEVERS", None)
        if default_retrievers:
            headers["retrievers"] = default_retrievers
        else:
            # Fall back to default retrievers: internal_biblio, internal_highlight, internal_file, noteexpress, tavily
            headers["retrievers"] = "internal_biblio,internal_highlight,internal_file,noteexpress,tavily"
    
    # Update request headers
    research_request.headers = headers
    
    # Add background task to generate report
    background_tasks.add_task(write_report, research_request, research_id, logs_handler)
    
    # Return immediately with task_id
    return {
        "message": "Report generation task has been submitted.",
        "research_id": research_id,
        "status": "processing",
        "json_path": os.path.relpath(logs_handler.log_file)
    }


@app.get("/files/")
async def list_files():
    if not os.path.exists(DOC_PATH):
        os.makedirs(DOC_PATH, exist_ok=True)
    files = os.listdir(DOC_PATH)
    print(f"Files in {DOC_PATH}: {files}")
    return {"files": files}


@app.post("/api/multi_agents")
async def run_multi_agents():
    return await execute_multi_agents(manager)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return await handle_file_upload(file, DOC_PATH)


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    return await handle_file_deletion(filename, DOC_PATH)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await handle_websocket_communication(websocket, manager)
    except WebSocketDisconnect as e:
        # Disconnect with more detailed logging about the WebSocket disconnect reason
        logger.info(f"WebSocket disconnected with code {e.code} and reason: '{e.reason}'")
        await manager.disconnect(websocket)
    except Exception as e:
        # More general exception handling
        logger.error(f"Unexpected WebSocket error: {str(e)}")
        await manager.disconnect(websocket)

@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    """Process a chat request with a report and message history.

    Args:
        chat_request: ChatRequest object containing report text and message history

    Returns:
        JSON response with the assistant's message and any tool usage metadata
    """
    try:
        logger.info(f"Received chat request with {len(chat_request.messages)} messages")

        # Create chat agent with the report
        chat_agent = ChatAgentWithMemory(
            report=chat_request.report,
            config_path="default",
            headers=None
        )

        # Process the chat and get response with metadata
        response_content, tool_calls_metadata = await chat_agent.chat(chat_request.messages, None)
        logger.info(f"response_content: {response_content}")
        logger.info(f"Got chat response of length: {len(response_content) if response_content else 0}")
        
        if tool_calls_metadata:
            logger.info(f"Tool calls used: {json.dumps(tool_calls_metadata)}")

        # Format response as a ChatMessage object with role, content, timestamp and metadata
        response_message = {
            "role": "assistant",
            "content": response_content,
            "timestamp": int(time.time() * 1000),  # Current time in milliseconds
            "metadata": {
                "tool_calls": tool_calls_metadata
            } if tool_calls_metadata else None
        }

        logger.info(f"Returning formatted response: {json.dumps(response_message)[:100]}...")
        return {"response": response_message}
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return {"error": str(e)}

@app.post("/api/reports/{research_id}/chat")
async def research_report_chat(research_id: str, request: Request):
    """Handle chat requests for a specific research report.
    Directly processes the raw request data to avoid validation errors.
    """
    try:
        # Get raw JSON data from request
        data = await request.json()
        
        # Create chat agent with the report
        chat_agent = ChatAgentWithMemory(
            report=data.get("report", ""),
            config_path="default",
            headers=None
        )

        # Process the chat and get response with metadata
        response_content, tool_calls_metadata = await chat_agent.chat(data.get("messages", []), None)
        
        if tool_calls_metadata:
            logger.info(f"Tool calls used: {json.dumps(tool_calls_metadata)}")

        # Format response as a ChatMessage object
        response_message = {
            "role": "assistant",
            "content": response_content,
            "timestamp": int(time.time() * 1000),
            "metadata": {
                "tool_calls": tool_calls_metadata
            } if tool_calls_metadata else None
        }

        return {"response": response_message}
    except Exception as e:
        logger.error(f"Error in research report chat: {str(e)}", exc_info=True)
        return {"error": str(e)}

@app.put("/api/reports/{research_id}")
async def update_report(research_id: str, request: Request):
    """Update a specific research report by ID - no database configured."""
    logger.debug(f"Update requested for report {research_id} - no database configured, not persisted")
    return {"success": True, "id": research_id}

@app.delete("/api/reports/{research_id}")
async def delete_report(research_id: str):
    """Delete a specific research report by ID - no database configured."""
    logger.debug(f"Delete requested for report {research_id} - no database configured, nothing to delete")
    return {"success": True, "id": research_id}


# Task status endpoint removed - no longer using Celery
