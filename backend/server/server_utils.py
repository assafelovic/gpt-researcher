import asyncio
import json
import os
import re
import time
import shutil
import traceback
from typing import Awaitable, Dict, List, Any
from fastapi.responses import JSONResponse, FileResponse
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher import GPTResearcher
from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
import logging
import unicodedata

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CustomLogsHandler:
    """Custom handler to capture streaming logs from the research process"""
    def __init__(self, websocket, task: str):
        self.logs = []
        self.websocket = websocket
        sanitized_filename = sanitize_filename(f"task_{int(time.time())}_{task}")
        self.log_file = os.path.join("outputs", f"{sanitized_filename}.json")
        self.timestamp = datetime.now().isoformat()
        # Initialize log file with metadata
        os.makedirs("outputs", exist_ok=True)
        with open(self.log_file, 'w') as f:
            json.dump({
                "timestamp": self.timestamp,
                "events": [],
                "content": {
                    "query": "",
                    "sources": [],
                    "context": [],
                    "report": "",
                    "costs": 0.0
                }
            }, f, indent=2)

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Store log data and send to websocket"""
        # Send to websocket for real-time display
        if self.websocket:
            await self.websocket.send_json(data)
            
        # Read current log file
        with open(self.log_file, 'r') as f:
            log_data = json.load(f)
            
        # Update appropriate section based on data type
        if data.get('type') == 'logs':
            log_data['events'].append({
                "timestamp": datetime.now().isoformat(),
                "type": "event",
                "data": data
            })
        else:
            # Update content section for other types of data
            log_data['content'].update(data)
            
        # Save updated log file
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        logger.debug(f"Log entry written to: {self.log_file}")


class Researcher:
    def __init__(self, query: str, report_type: str = "research_report"):
        self.query = query
        self.report_type = report_type
        # Generate unique ID for this research task
        self.research_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query)}"
        # Initialize logs handler with research ID
        self.logs_handler = CustomLogsHandler(None, self.research_id)
        self.researcher = GPTResearcher(
            query=query,
            report_type=report_type,
            websocket=self.logs_handler
        )

    async def research(self) -> dict:
        """Conduct research and return paths to generated files"""
        await self.researcher.conduct_research()
        report = await self.researcher.write_report()
        
        # Generate the files
        sanitized_filename = sanitize_filename(f"task_{int(time.time())}_{self.query}")
        file_paths = await generate_report_files(report, sanitized_filename)
        
        # Get the JSON log path that was created by CustomLogsHandler
        json_relative_path = os.path.relpath(self.logs_handler.log_file)
        
        return {
            "output": {
                **file_paths,  # Include PDF, DOCX, and MD paths
                "json": json_relative_path
            }
        }

def sanitize_filename(filename: str) -> str:
    # Split into components
    prefix, timestamp, *task_parts = filename.split('_')
    task = '_'.join(task_parts)
    
    # Calculate max length for task portion
    # 255 - len(os.getcwd()) - len("\\gpt-researcher\\outputs\\") - len("task_") - len(timestamp) - len("_.json") - safety_margin
    max_task_length = 255 - len(os.getcwd()) - 24 - 5 - 10 - 6 - 5  # ~189 chars for task
    
    # Truncate task if needed (by bytes)
    truncated_task = ""
    byte_count = 0
    for char in task:
        char_bytes = len(char.encode('utf-8'))
        if byte_count + char_bytes <= max_task_length:
            truncated_task += char
            byte_count += char_bytes
        else:
            break

    # Reassemble and clean the filename
    sanitized = f"{prefix}_{timestamp}_{truncated_task}"
    return re.sub(r"[^\w-]", "", sanitized).strip()


async def handle_start_command(websocket, data: str, manager):
    json_data = json.loads(data[6:])
    (
        task,
        report_type,
        source_urls,
        document_urls,
        tone,
        headers,
        report_source,
        query_domains,
        mcp_enabled,
        mcp_strategy,
        mcp_configs,
    ) = extract_command_data(json_data)

    if not task or not report_type:
        print("❌ Error: Missing task or report_type")
        await websocket.send_json({
            "type": "logs",
            "content": "error", 
            "output": f"Missing required parameters - task: {task}, report_type: {report_type}"
        })
        return

    # Create logs handler with websocket and task
    logs_handler = CustomLogsHandler(websocket, task)
    # Initialize log content with query
    await logs_handler.send_json({
        "query": task,
        "sources": [],
        "context": [],
        "report": ""
    })

    sanitized_filename = sanitize_filename(f"task_{int(time.time())}_{task}")

    report = await manager.start_streaming(
        task,
        report_type,
        report_source,
        source_urls,
        document_urls,
        tone,
        websocket,
        headers,
        query_domains,
        mcp_enabled,
        mcp_strategy,
        mcp_configs,
    )
    report = str(report)
    file_paths = await generate_report_files(report, sanitized_filename)
    # Add JSON log path to file_paths
    file_paths["json"] = os.path.relpath(logs_handler.log_file)
    await send_file_paths(websocket, file_paths)


async def handle_human_feedback(data: str):
    feedback_data = json.loads(data[14:])  # Remove "human_feedback" prefix
    print(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state

async def handle_chat(websocket, data: str, manager):
    json_data = json.loads(data[4:])
    print(f"Received chat message: {json_data.get('message')}")
    await manager.chat(json_data.get("message"), websocket)

async def generate_report_files(report: str, filename: str) -> Dict[str, str]:
    pdf_path = await write_md_to_pdf(report, filename)
    docx_path = await write_md_to_word(report, filename)
    md_path = await write_text_to_md(report, filename)
    return {"pdf": pdf_path, "docx": docx_path, "md": md_path}


async def send_file_paths(websocket, file_paths: Dict[str, str]):
    await websocket.send_json({"type": "path", "output": file_paths})


def get_config_dict(
    langchain_api_key: str, openai_api_key: str, tavily_api_key: str,
    google_api_key: str, google_cx_key: str, bing_api_key: str,
    searchapi_api_key: str, serpapi_api_key: str, serper_api_key: str, searx_url: str
) -> Dict[str, str]:
    return {
        "LANGCHAIN_API_KEY": langchain_api_key or os.getenv("LANGCHAIN_API_KEY", ""),
        "OPENAI_API_KEY": openai_api_key or os.getenv("OPENAI_API_KEY", ""),
        "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", ""),
        "TAVILY_API_KEY": tavily_api_key or os.getenv("TAVILY_API_KEY", ""),
        "GOOGLE_API_KEY": google_api_key or os.getenv("GOOGLE_API_KEY", ""),
        "GOOGLE_CX_KEY": google_cx_key or os.getenv("GOOGLE_CX_KEY", ""),
        "BING_API_KEY": bing_api_key or os.getenv("BING_API_KEY", ""),
        "SEARCHAPI_API_KEY": searchapi_api_key or os.getenv("SEARCHAPI_API_KEY", ""),
        "SERPAPI_API_KEY": serpapi_api_key or os.getenv("SERPAPI_API_KEY", ""),
        "SERPER_API_KEY": serper_api_key or os.getenv("SERPER_API_KEY", ""),
        "SEARX_URL": searx_url or os.getenv("SEARX_URL", ""),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
        "DOC_PATH": os.getenv("DOC_PATH", "./my-docs"),
        "RETRIEVER": os.getenv("RETRIEVER", ""),
        "EMBEDDING_MODEL": os.getenv("OPENAI_EMBEDDING_MODEL", "")
    }


def update_environment_variables(config: Dict[str, str]):
    for key, value in config.items():
        os.environ[key] = value


def secure_filename(filename: str) -> str:
    """
    Securely sanitize a filename to prevent path traversal attacks.
    
    Args:
        filename: The original filename
        
    Returns:
        A sanitized filename safe for filesystem operations
        
    Raises:
        ValueError: If the filename is invalid or potentially malicious
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Check for path traversal attempts before any processing
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Filename contains path traversal sequences")
    
    # Remove null bytes and other control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Normalize unicode to prevent unicode-based attacks
    filename = unicodedata.normalize('NFKC', filename)
    
    # Remove tilde characters (home directory references)
    filename = filename.replace('~', '')
    
    # Remove drive letters (Windows)
    if len(filename) > 1 and filename[1] == ':':
        filename = filename[2:]
    
    # Remove leading dots and spaces
    filename = filename.lstrip('. ')
    
    # Ensure filename is not empty after sanitization
    if not filename:
        raise ValueError("Filename becomes empty after sanitization")
    
    # Check for reserved names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
        'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = filename.split('.')[0].upper()
    if name_without_ext in reserved_names:
        raise ValueError(f"Filename '{filename}' uses a reserved name")
    
    # Limit filename length (most filesystems support 255 chars)
    if len(filename.encode('utf-8')) > 255:
        raise ValueError("Filename too long")
    
    return filename

def validate_file_path(file_path: str, base_path: str) -> str:
    """
    Validate that a file path is within the allowed base directory.
    
    Args:
        file_path: The file path to validate
        base_path: The base directory that should contain the file
        
    Returns:
        The resolved absolute path if valid
        
    Raises:
        ValueError: If the path is outside the base directory
    """
    # Convert to absolute paths and resolve any symlinks/relative components
    abs_base = os.path.abspath(base_path)
    abs_file = os.path.abspath(file_path)
    
    # Ensure the file path is within the base directory
    if not abs_file.startswith(abs_base + os.sep) and abs_file != abs_base:
        raise ValueError(f"File path '{file_path}' is outside allowed directory '{base_path}'")
    
    return abs_file

async def handle_file_upload(file, DOC_PATH: str) -> Dict[str, str]:
    """
    Handle file upload with security validation to prevent path traversal attacks.
    
    Args:
        file: The uploaded file object
        DOC_PATH: The base directory for file storage
        
    Returns:
        Dict containing filename and path information
        
    Raises:
        HTTPException: If the file upload is invalid or potentially malicious
    """
    try:
        # Validate and sanitize the filename
        safe_filename = secure_filename(file.filename)
        
        # Create the full file path
        file_path = os.path.join(DOC_PATH, safe_filename)
        
        # Validate the path is within the allowed directory
        validated_path = validate_file_path(file_path, DOC_PATH)
        
        # Ensure the DOC_PATH directory exists
        os.makedirs(DOC_PATH, exist_ok=True)
        
        # Check if file already exists and handle accordingly
        if os.path.exists(validated_path):
            # Generate a unique filename to avoid conflicts
            name, ext = os.path.splitext(safe_filename)
            counter = 1
            while os.path.exists(validated_path):
                new_filename = f"{name}_{counter}{ext}"
                file_path = os.path.join(DOC_PATH, new_filename)
                validated_path = validate_file_path(file_path, DOC_PATH)
                counter += 1
            safe_filename = new_filename
        
        # Write the file securely
        with open(validated_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded securely to {validated_path}")
        
        # Load the document
        document_loader = DocumentLoader(DOC_PATH)
        await document_loader.load()
        
        return {"filename": safe_filename, "path": validated_path}
        
    except ValueError as e:
        logger.error(f"File upload validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid file: {str(e)}")
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

async def handle_file_deletion(filename: str, DOC_PATH: str) -> JSONResponse:
    """
    Handle file deletion with security validation to prevent path traversal attacks.
    
    Args:
        filename: The filename to delete
        DOC_PATH: The base directory for file storage
        
    Returns:
        JSONResponse indicating success or failure
    """
    try:
        # Validate and sanitize the filename
        safe_filename = secure_filename(filename)
        
        # Create the full file path
        file_path = os.path.join(DOC_PATH, safe_filename)
        
        # Validate the path is within the allowed directory
        validated_path = validate_file_path(file_path, DOC_PATH)
        
        # Check if file exists and delete it
        if os.path.exists(validated_path):
            # Additional security check: ensure it's a file, not a directory
            if not os.path.isfile(validated_path):
                logger.error(f"Attempted to delete non-file: {validated_path}")
                return JSONResponse(
                    status_code=400, 
                    content={"message": "Cannot delete: not a file"}
                )
            
            os.remove(validated_path)
            logger.info(f"File deleted securely: {validated_path}")
            return JSONResponse(content={"message": "File deleted successfully"})
        else:
            logger.warning(f"File not found for deletion: {validated_path}")
            return JSONResponse(
                status_code=404, 
                content={"message": "File not found"}
            )
            
    except ValueError as e:
        logger.error(f"File deletion validation error: {e}")
        return JSONResponse(
            status_code=400, 
            content={"message": f"Invalid filename: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"File deletion error: {e}")
        return JSONResponse(
            status_code=500, 
            content={"message": "File deletion failed"}
        )


async def execute_multi_agents(manager) -> Any:
    websocket = manager.active_connections[0] if manager.active_connections else None
    if websocket:
        report = await run_research_task("Is AI in a hype cycle?", websocket, stream_output)
        return {"report": report}
    else:
        return JSONResponse(status_code=400, content={"message": "No active WebSocket connection"})


async def handle_websocket_communication(websocket, manager):
    running_task: asyncio.Task | None = None

    def run_long_running_task(awaitable: Awaitable) -> asyncio.Task:
        async def safe_run():
            try:
                await awaitable
            except asyncio.CancelledError:
                logger.info("Task cancelled.")
                raise
            except Exception as e:
                logger.error(f"Error running task: {e}\n{traceback.format_exc()}")
                await websocket.send_json(
                    {
                        "type": "logs",
                        "content": "error",
                        "output": f"Error: {e}",
                    }
                )

        return asyncio.create_task(safe_run())

    try:
        while True:
            try:
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_text("pong")
                elif running_task and not running_task.done():
                    # discard any new request if a task is already running
                    logger.warning(
                        f"Received request while task is already running. Request data preview: {data[: min(20, len(data))]}..."
                    )
                    websocket.send_json(
                        {
                            "types": "logs",
                            "output": "Task already running. Please wait.",
                        }
                    )
                elif data.startswith("start"):
                    running_task = run_long_running_task(
                        handle_start_command(websocket, data, manager)
                    )
                elif data.startswith("human_feedback"):
                    running_task = run_long_running_task(handle_human_feedback(data))
                elif data.startswith("chat"):
                    running_task = run_long_running_task(
                        handle_chat(websocket, data, manager)
                    )
                else:
                    print("Error: Unknown command or not enough parameters provided.")
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
    finally:
        if running_task and not running_task.done():
            running_task.cancel()

def extract_command_data(json_data: Dict) -> tuple:
    return (
        json_data.get("task"),
        json_data.get("report_type"),
        json_data.get("source_urls"),
        json_data.get("document_urls"),
        json_data.get("tone"),
        json_data.get("headers", {}),
        json_data.get("report_source"),
        json_data.get("query_domains", []),
        json_data.get("mcp_enabled", False),
        json_data.get("mcp_strategy", "fast"),
        json_data.get("mcp_configs", []),
    )
