import json
import os
from typing import Dict, List, Any
import time
import logging
import sys
import warnings
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

from server.websocket_manager import run_agent
from utils import write_md_to_word, write_md_to_pdf
from gpt_researcher.utils.enum import Tone
from chat.chat import ChatAgentWithMemory

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
    user_id: str | None = None  # User ID (can also be in headers)
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


async def write_report(research_request: ResearchRequest, research_id: str = None):
    try:
        # Extract user_id from request (can be in user_id field or headers)
        user_id = research_request.user_id or research_request.headers.get("user_id") if research_request.headers else None

        report_information = await run_agent(
            task=research_request.task,
            report_type=research_request.report_type,
            report_source=research_request.report_source,
            source_urls=[],
            document_urls=[],
            tone=Tone[research_request.tone],
            websocket=None,
            stream_output=None,
            headers=research_request.headers,
            query_domains=[],
            config_path="",
            return_researcher=True
        )

        docx_path = await write_md_to_word(report_information[0], research_id)
        pdf_path = await write_md_to_pdf(report_information[0], research_id)
        if research_request.report_type != "multi_agents":
            report, researcher = report_information
            response = {
                "research_id": research_id,
                "research_information": {
                    "source_urls": researcher.get_source_urls(),
                    "research_costs": researcher.get_costs(),
                    "token_usage": researcher.get_token_usage(),
                    "visited_urls": list(researcher.visited_urls),
                    "research_images": researcher.get_research_images(),
                    # "research_sources": researcher.get_research_sources(),  # Raw content of sources may be very large
                },
                "report": report,
                "docx_path": docx_path,
                "pdf_path": pdf_path
            }
        else:
            response = { "research_id": research_id, "report": "", "docx_path": docx_path, "pdf_path": pdf_path }

        # Send webhook notification (if configured in environment)
        await send_webhook_notification(
            research_id=research_id,
            user_id=user_id,
            status="completed",
            response=response
        )

        return response
    except Exception as e:
        # Extract user_id from request for error webhook
        user_id = research_request.user_id or research_request.headers.get("user_id") if research_request.headers else None
        
        # Send error webhook (if configured in environment)
        await send_webhook_notification(
            research_id=research_id,
            user_id=user_id,
            status="failed",
            error=str(e)
        )
        raise


async def send_webhook_notification(
    research_id: str,
    status: str,
    response: Dict[str, Any] = None,
    error: str = None,
    user_id: str = None
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
        user_id: The user ID from the research request (optional)
    """
    # Get webhook URL from environment variable
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        # Webhook not configured, skip notification
        return
    
    try:
        payload = {
            "research_id": research_id,
            "status": status,
            "timestamp": time.time()
        }
        
        # Add user_id if provided
        if user_id:
            payload["user_id"] = user_id
        
        if status == "completed" and response:
            payload["data"] = {
                "report": response.get("report", ""),
                "docx_path": response.get("docx_path"),
                "pdf_path": response.get("pdf_path"),
                "research_information": response.get("research_information", {})
            }
        elif status == "failed" and error:
            payload["error"] = error
        
        # Prepare request headers with API key if configured
        headers = {}
        webhook_api_key = os.getenv("WEBHOOK_API_KEY")
        if webhook_api_key:
            headers["x-api-key"] = webhook_api_key
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            result = await client.post(webhook_url, json=payload, headers=headers)
            result.raise_for_status()
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

    research_id = sanitize_filename(f"task_{int(time.time())}_{research_request.task}")

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
    background_tasks.add_task(write_report, research_request, research_id)

    # Return immediately with task_id
    return {
        "message": "Report generation task has been submitted.",
        "research_id": research_id,
        "status": "processing"
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
