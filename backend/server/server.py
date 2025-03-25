import json
import os
from typing import Dict, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend.server.websocket_manager import WebSocketManager
from backend.server.server_utils import (
    get_config_dict,
    update_environment_variables, handle_file_upload, handle_file_deletion,
    execute_multi_agents, handle_websocket_communication
)

from backend.utils import export_pdf, export_docx
from fastapi import Response, HTTPException

from gpt_researcher.utils.logging_config import setup_research_logging

import logging

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
    GOOGLE_API_KEY: str = ''
    GOOGLE_CX_KEY: str = ''
    BING_API_KEY: str = ''
    SEARCHAPI_API_KEY: str = ''
    SERPAPI_API_KEY: str = ''
    SERPER_API_KEY: str = ''
    SEARX_URL: str = ''
    XAI_API_KEY: str
    DEEPSEEK_API_KEY: str


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
    

# Routes


# Keep this for testing and development purposes
# @app.get("/")
# async def read_root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request, "report": None})

@app.post("/export_file")
async def export_file(request: Request):
    """
    Generate a file from the content and format
    Args:
        request: Request object
    Returns:
        bytes: The file buffer
    """
    
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or auth_header != os.getenv("GPT_RESEARCHER_AUTH_TOKEN"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    format = data.get("format")
    content = data.get("content")
    
    try:
        logger.info(f"Generating {format} file from content")
        
        if format.lower() == "pdf":
            file_buffer = await export_pdf(content)
            media_type = "application/pdf"
            
        elif format.lower() == "docx":
            file_buffer = await export_docx(content)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        else:
            raise Exception(f"Unsupported format: {format}")
        
        return Response(
            content=file_buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=generated.{format.lower()}"
            }
        )
            
        
    except Exception as e:
        logger.error(f"Error generating file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/output_file")
async def delete_output_file(path: str): 
    filename = os.path.basename(path)
    return await handle_file_deletion(filename, "outputs")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
        
    await manager.connect(websocket)
    try:
        await handle_websocket_communication(websocket, manager)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
