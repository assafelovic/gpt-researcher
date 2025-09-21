from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import sys
import os
from contextlib import asynccontextmanager

# Add the parent directory to sys.path to make sure we can import from server
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.websocket_manager import WebSocketManager
from server.server_utils import handle_websocket_communication
from chat.chat import ChatAgentWithMemory
from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import Request, HTTPException
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Silence uvicorn reload logs
logging.getLogger("uvicorn.supervisors.ChangeReload").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Research API starting up - no database required")
    yield
    # Shutdown
    logging.info("Research API shutting down")

app = FastAPI(title="Research API", lifespan=lifespan)

# WebSocket manager
manager = WebSocketManager()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No database routers needed since we removed MongoDB

# Chat request model
class ChatRequest(BaseModel):
    report: str
    messages: List[Dict[str, Any]]
    
    class Config:
        extra = "allow"  # Allow extra fields in the request

# Lifespan events now handled in the lifespan context manager above


@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    """Process a chat request with a report and message history.

    Args:
        chat_request: ChatRequest object containing report text and message history

    Returns:
        JSON response with the assistant's message and any tool usage metadata
    """
    try:
        logging.info(f"Received chat request with {len(chat_request.messages)} messages")

        # Create chat agent with the report
        chat_agent = ChatAgentWithMemory(
            report=chat_request.report,
            config_path="default",
            headers=None
        )

        # Process the chat and get response with metadata
        response_content, tool_calls_metadata = await chat_agent.chat(chat_request.messages, None)
        logging.info(f"response_content: {response_content}")
        logging.info(f"Got chat response of length: {len(response_content) if response_content else 0}")
        
        if tool_calls_metadata:
            logging.info(f"Tool calls used: {json.dumps(tool_calls_metadata)}")

        # Format response as a ChatMessage object with role, content, timestamp and metadata
        response_message = {
            "role": "assistant",
            "content": response_content,
            "timestamp": int(time.time() * 1000),  # Current time in milliseconds
            "metadata": {
                "tool_calls": tool_calls_metadata
            } if tool_calls_metadata else None
        }

        logging.info(f"Returning formatted response: {json.dumps(response_message)[:100]}...")
        return {"response": response_message}
    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return {"error": str(e)}


@app.get("/api/reports")
async def get_all_reports(report_ids: str = None):
    """Get research reports - returns empty list since no database."""
    logging.info("No database configured - returning empty reports list")
    return {"reports": []}

@app.get("/api/reports/{research_id}")
async def get_report_by_id(research_id: str):
    """Get a specific research report by ID - no database configured."""
    logging.info(f"No database configured - cannot retrieve report {research_id}")
    raise HTTPException(status_code=404, detail="Report not found - no database configured")

@app.post("/api/reports")
async def create_or_update_report(request: Request):
    """Create or update a research report - no database persistence."""
    try:
        data = await request.json()
        research_id = data.get("id", "temp_id")
        logging.info(f"Report creation requested for ID: {research_id} - no database configured, not persisted")
        return {"success": True, "id": research_id}
    except Exception as e:
        logging.error(f"Error processing report creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/reports/{research_id}")
async def update_report(research_id: str, request: Request):
    """Update a specific research report by ID - no database configured."""
    logging.info(f"Update requested for report {research_id} - no database configured, not persisted")
    return {"success": True, "id": research_id}

@app.delete("/api/reports/{research_id}")
async def delete_report(research_id: str):
    """Delete a specific research report by ID - no database configured."""
    logging.info(f"Delete requested for report {research_id} - no database configured, nothing to delete")
    return {"success": True, "id": research_id}

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
            logging.info(f"Tool calls used: {json.dumps(tool_calls_metadata)}")

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
        logging.error(f"Error in research report chat: {str(e)}", exc_info=True)
        return {"error": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time research communication."""
    await manager.connect(websocket)
    try:
        await handle_websocket_communication(websocket, manager)
    except WebSocketDisconnect as e:
        # Disconnect with more detailed logging about the WebSocket disconnect reason
        logging.info(f"WebSocket disconnected with code {e.code} and reason: '{e.reason}'")
        await manager.disconnect(websocket)
    except Exception as e:
        # More general exception handling
        logging.error(f"Unexpected WebSocket error: {str(e)}")
        await manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 