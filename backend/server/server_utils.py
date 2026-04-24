import asyncio
import json
import logging
import os
import re
import time
import shutil
import threading
import traceback
import uuid
from typing import Awaitable, Dict, List, Any
from fastapi.responses import JSONResponse, FileResponse
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher import GPTResearcher
from utils import write_md_to_pdf, write_md_to_word, write_text_to_md
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
import hashlib
from gpt_researcher.research_run_store import (
    get_outputs_dir,
    get_research_run_store,
    jsonable,
)

logger = logging.getLogger(__name__)

from .multi_agent_runner import run_multi_agent_task
from .hlt_extensions import prepare_research_request as prepare_hlt_research_request

# Import chat agent
try:
    import sys
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from chat.chat import ChatAgentWithMemory
except ImportError:
    ChatAgentWithMemory = None

class CustomLogsHandler:
    """Custom handler to capture streaming logs from the research process"""
    def __init__(self, websocket, task: str, research_id: str | None = None):
        self.logs = []
        self.websocket = websocket
        self.research_id = research_id or generate_research_id(task)
        self.run_id = self.research_id
        sanitized_filename = sanitize_filename(f"task_{int(time.time())}_{self.research_id}_{task}")
        output_dir = get_outputs_dir()
        self.log_file = str(output_dir / f"{sanitized_filename}.json")
        self.timestamp = datetime.now().isoformat()
        self._lock = threading.Lock()

        # Initialize log file with metadata
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, "w") as f:
            json.dump(self._initial_log_data(), f, indent=2)

    def _initial_log_data(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "research_id": self.research_id,
            "run_id": self.run_id,
            "events": [],
            "content": {
                "query": "",
                "sources": [],
                "context": [],
                "report": "",
                "costs": 0.0,
            },
        }

    def _with_run_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(data)
        enriched.setdefault("research_id", self.research_id)
        enriched.setdefault("run_id", self.run_id)
        return enriched

    def _read_log_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.log_file):
            return self._initial_log_data()

        try:
            with open(self.log_file, "r") as f:
                content = f.read()
            log_data = json.loads(content) if content.strip() else self._initial_log_data()
        except json.JSONDecodeError:
            corrupt_path = f"{self.log_file}.corrupt.{int(time.time())}"
            try:
                os.replace(self.log_file, corrupt_path)
                logger.warning(
                    "Preserved corrupt research log and reinitialized it",
                    extra={"research_id": self.research_id, "corrupt_path": corrupt_path},
                )
            except OSError:
                logger.warning("Failed to preserve corrupt research log", exc_info=True)
            return self._initial_log_data()

        log_data.setdefault("timestamp", self.timestamp)
        log_data.setdefault("research_id", self.research_id)
        log_data.setdefault("run_id", self.run_id)
        log_data.setdefault("events", [])
        log_data.setdefault("content", self._initial_log_data()["content"])
        return log_data

    def _write_log_data(self, log_data: Dict[str, Any]) -> None:
        tmp_path = f"{self.log_file}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        with open(tmp_path, "w") as f:
            f.write(json.dumps(log_data, indent=2))
        os.replace(tmp_path, self.log_file)

    def _persist_log_event(self, enriched_data: Dict[str, Any]) -> None:
        with self._lock:
            log_data = self._read_log_data()

            # Update appropriate section based on data type
            if enriched_data.get("type") == "logs":
                log_data["events"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "event",
                    "data": enriched_data,
                })
                content_update = {
                    key: enriched_data[key]
                    for key in ("query", "sources", "context", "report", "costs")
                    if key in enriched_data
                }
                if content_update:
                    log_data["content"].update(content_update)
            else:
                # Update content section for other types of data
                log_data["content"].update(enriched_data)

            self._write_log_data(log_data)

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Store log data and send to websocket"""
        enriched_data = self._with_run_metadata(data)

        # Send to websocket for real-time display
        if self.websocket:
            try:
                await self.websocket.send_json(enriched_data)
            except Exception:
                logger.warning(
                    "Failed to send WebSocket log event",
                    extra={"research_id": self.research_id},
                    exc_info=True,
                )

        try:
            await asyncio.to_thread(self._persist_log_event, enriched_data)
        except Exception:
            logger.warning(
                "Failed to persist research log event",
                extra={"research_id": self.research_id, "log_file": self.log_file},
                exc_info=True,
            )


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
    task_hash = hashlib.md5(task.encode('utf-8', errors='ignore')).hexdigest()[:10]
            
    # Reassemble and clean the filename
    sanitized = f"{prefix}_{timestamp}_{task_hash}"
    return re.sub(r"[^\w\s-]", "", sanitized).strip()


_WINDOWS_RESERVED_FILENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def secure_filename(filename: str) -> str:
    """Return a safe single filename or raise ValueError."""

    if not isinstance(filename, str):
        raise ValueError("Filename must be a string")

    candidate = filename.replace("\\", "/").strip()
    if not candidate:
        raise ValueError("Filename is empty")

    if any(part == ".." for part in candidate.split("/")):
        raise ValueError("Filename contains path traversal")

    candidate = re.sub(r"^[A-Za-z]:", "", candidate)
    candidate = re.sub(r"[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]", "", candidate)
    candidate = candidate.replace("/", "")
    candidate = re.sub(r"[^A-Za-z0-9._ -]", "", candidate)
    candidate = candidate.lstrip(" .").rstrip(" .")

    if not candidate:
        raise ValueError("Filename is empty")

    stem = Path(candidate).stem.upper()
    if stem in _WINDOWS_RESERVED_FILENAMES:
        raise ValueError("Filename uses a reserved name")

    if len(candidate.encode("utf-8")) > 255:
        raise ValueError("Filename is too long")

    return candidate


def validate_file_path(file_path: str, base_dir: str) -> str:
    """Resolve `file_path` and guarantee it stays inside `base_dir`."""

    base = os.path.realpath(base_dir)
    resolved = os.path.realpath(file_path)

    if os.path.commonpath([base, resolved]) != base:
        raise ValueError("File path is outside allowed directory")

    return resolved


def generate_research_id(task: str) -> str:
    task_hash = hashlib.md5(task.encode("utf-8", errors="ignore")).hexdigest()[:10]
    return f"research_{int(time.time())}_{task_hash}_{uuid.uuid4().hex[:8]}"


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
        max_search_results,
        hlt_research_scope,
    ) = extract_command_data(json_data)

    if not task or not report_type:
        logger.error("Missing task or report_type")
        return

    display_task = task
    research_id = json_data.get("research_id") or generate_research_id(display_task)

    # Create logs handler with websocket and task
    logs_handler = CustomLogsHandler(websocket, display_task, research_id=research_id)
    (
        task,
        mcp_enabled,
        mcp_strategy,
        mcp_configs,
        hlt_scope_metadata,
        scraper_override,
    ) = prepare_hlt_research_request(
        task=display_task,
        mcp_enabled=mcp_enabled,
        mcp_strategy=mcp_strategy,
        mcp_configs=mcp_configs,
        research_scope=hlt_research_scope,
    )
    run_store = get_research_run_store()
    run_store.create_run(
        research_id,
        query=display_task,
        report_type=report_type,
        report_source=report_source,
        tone=tone,
        status="running",
        hlt_research_scope=hlt_scope_metadata,
    )

    # Initialize log content with query
    await logs_handler.send_json({
        "type": "logs",
        "content": "research_started",
        "output": f"Research started: {display_task}",
        "query": display_task,
        "sources": [],
        "context": [],
        "report": "",
        "metadata": {
            "research_id": research_id,
            "run_id": research_id,
            "hlt_research_scope": hlt_scope_metadata,
        },
    })
    await logs_handler.send_json({
        "type": "logs",
        "content": "hlt_scope_status",
        "output": "HLT research scope resolved",
        "metadata": {
            "research_id": research_id,
            "run_id": research_id,
            "hlt_research_scope": hlt_scope_metadata,
        },
    })

    sanitized_filename = sanitize_filename(f"task_{int(time.time())}_{display_task}")

    try:
        report_result = await manager.start_streaming(
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
            max_search_results,
            logs_handler=logs_handler,
            return_researcher=True,
            scraper_override=scraper_override,
        )
    except Exception as e:
        logger.error(
            "Error running research task",
            extra={"research_id": research_id},
            exc_info=True,
        )
        await logs_handler.send_json({
            "type": "logs",
            "content": "error",
            "output": f"Error: {e}",
        })
        run_store.fail_run(research_id, error_code="runtime_error", error_message=str(e))
        return

    researcher = None
    if isinstance(report_result, tuple) and len(report_result) == 2:
        report, researcher = report_result
    else:
        report = report_result
    report = str(report)
    file_paths = await generate_report_files(report, sanitized_filename)
    # Add JSON log path to file_paths
    file_paths["json"] = os.path.relpath(logs_handler.log_file)
    file_paths["research_id"] = research_id
    file_paths["run_id"] = research_id
    sources = jsonable(researcher.get_research_sources()) if researcher else []
    source_urls = list(researcher.get_source_urls()) if researcher else []
    costs = researcher.get_costs() if researcher else 0.0
    run_store.complete_run(
        research_id,
        context=jsonable(researcher.get_research_context()) if researcher else [],
        sources=sources,
        source_urls=source_urls,
        costs=costs,
        report_path=file_paths.get("md"),
        md_path=file_paths.get("md"),
        pdf_path=file_paths.get("pdf"),
        docx_path=file_paths.get("docx"),
        hlt_research_scope=hlt_scope_metadata,
    )
    await logs_handler.send_json({
        "type": "logs",
        "content": "research_completed",
        "output": "Research completed",
    })
    await send_file_paths(websocket, file_paths, research_id=research_id)


async def handle_human_feedback(data: str):
    feedback_data = json.loads(data[14:])  # Remove "human_feedback" prefix
    logger.info(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state


async def handle_chat_command(websocket, data: str):
    """Handle chat command from WebSocket."""
    try:
        # Parse chat data - format is "chat {json_data}"
        json_str = data[5:].strip()  # Remove "chat " prefix
        chat_data = json.loads(json_str)
        
        message = chat_data.get("message", "")
        report = chat_data.get("report", "")
        messages = chat_data.get("messages", [])
        
        # If only message is provided, convert to messages format
        if message and not messages:
            messages = [{"role": "user", "content": message}]
        
        if not messages:
            await websocket.send_json({
                "type": "chat",
                "content": "No message provided.",
                "role": "assistant"
            })
            return
        
        # Check if ChatAgentWithMemory is available
        if ChatAgentWithMemory is None:
            await websocket.send_json({
                "type": "chat",
                "content": "Chat functionality is not available. Please check the server configuration.",
                "role": "assistant"
            })
            return
        
        # Create chat agent with the report context
        chat_agent = ChatAgentWithMemory(
            report=report,
            config_path="default",
            headers=None
        )
        
        # Process the chat
        response_content, tool_calls_metadata = await chat_agent.chat(messages, websocket)
        
        # Send response back via WebSocket
        await websocket.send_json({
            "type": "chat",
            "content": response_content,
            "role": "assistant",
            "metadata": {
                "tool_calls": tool_calls_metadata
            } if tool_calls_metadata else None
        })
        
        logger.info(f"Chat response sent successfully")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse chat data: {e}")
        await websocket.send_json({
            "type": "chat",
            "content": f"Error: Invalid message format - {str(e)}",
            "role": "assistant"
        })
    except Exception as e:
        logger.error(f"Error handling chat command: {e}\n{traceback.format_exc()}")
        await websocket.send_json({
            "type": "chat",
            "content": f"Error processing your message: {str(e)}",
            "role": "assistant"
        })

async def generate_report_files(report: str, filename: str) -> Dict[str, str]:
    pdf_path = await write_md_to_pdf(report, filename)
    docx_path = await write_md_to_word(report, filename)
    md_path = await write_text_to_md(report, filename)
    return {"pdf": pdf_path, "docx": docx_path, "md": md_path}


async def send_file_paths(websocket, file_paths: Dict[str, str], research_id: str | None = None):
    payload = {"type": "path", "output": file_paths}
    if research_id:
        payload["research_id"] = research_id
        payload["run_id"] = research_id
    await websocket.send_json(payload)


def get_config_dict(
    langchain_api_key: str, openai_api_key: str, tavily_api_key: str,
    google_api_key: str, google_cx_key: str, bing_api_key: str,
    searchapi_api_key: str, serpapi_api_key: str, serper_api_key: str, searx_url: str
) -> Dict[str, str]:
    return {
        "LANGCHAIN_API_KEY": langchain_api_key or os.getenv("LANGCHAIN_API_KEY", ""),
        "OPENAI_API_KEY": openai_api_key or os.getenv("OPENAI_API_KEY", ""),
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


async def handle_file_upload(file, DOC_PATH: str) -> Dict[str, str]:
    try:
        filename = secure_filename(file.filename or "")
        os.makedirs(DOC_PATH, exist_ok=True)

        stem, ext = os.path.splitext(filename)
        file_path = validate_file_path(os.path.join(DOC_PATH, filename), DOC_PATH)
        suffix = 1
        while os.path.exists(file_path):
            filename = f"{stem}_{suffix}{ext}"
            file_path = validate_file_path(os.path.join(DOC_PATH, filename), DOC_PATH)
            suffix += 1
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid file: {exc}") from exc

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    logger.info(f"File uploaded to {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": filename, "path": file_path}


async def handle_file_deletion(filename: str, DOC_PATH: str) -> JSONResponse:
    try:
        safe_filename = secure_filename(filename)
        file_path = validate_file_path(os.path.join(DOC_PATH, safe_filename), DOC_PATH)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"message": f"Invalid file: {exc}"})

    if os.path.exists(file_path):
        if not os.path.isfile(file_path):
            return JSONResponse(status_code=400, content={"message": "Path is not a file"})

        os.remove(file_path)
        logger.info(f"File deleted: {file_path}")
        return JSONResponse(content={"message": "File deleted successfully"})
    else:
        logger.warning(f"File not found: {file_path}")
        return JSONResponse(status_code=404, content={"message": "File not found"})


async def execute_multi_agents(manager) -> Any:
    websocket = manager.active_connections[0] if manager.active_connections else None
    if websocket:
        report = await run_multi_agent_task("Is AI in a hype cycle?", websocket, stream_output)
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
                logger.info(f"Received WebSocket message: {data[:50]}..." if len(data) > 50 else data)
                
                if data == "ping":
                    await websocket.send_text("pong")
                elif running_task and not running_task.done():
                    # discard any new request if a task is already running
                    logger.warning(
                        f"Received request while task is already running. Request data preview: {data[: min(20, len(data))]}..."
                    )
                    await websocket.send_json(
                        {
                            "type": "logs",
                            "content": "warning",
                            "output": "Task already running. Please wait.",
                        }
                    )
                # Normalize command detection by checking startswith after stripping whitespace
                elif data.strip().startswith("start"):
                    logger.info(f"Processing start command")
                    running_task = run_long_running_task(
                        handle_start_command(websocket, data, manager)
                    )
                elif data.strip().startswith("human_feedback"):
                    logger.info(f"Processing human_feedback command")
                    running_task = run_long_running_task(handle_human_feedback(data))
                elif data.strip().startswith("chat"):
                    logger.info(f"Processing chat command")
                    running_task = run_long_running_task(handle_chat_command(websocket, data))
                else:
                    error_msg = f"Error: Unknown command or not enough parameters provided. Received: '{data[:100]}...'" if len(data) > 100 else f"Error: Unknown command or not enough parameters provided. Received: '{data}'"
                    logger.error(error_msg)
                    await websocket.send_json({
                        "type": "error",
                        "content": "error",
                        "output": "Unknown command received by server"
                    })
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}\n{traceback.format_exc()}")
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
        json_data.get("max_search_results"),
        json_data.get("hlt_research_scope"),
    )
