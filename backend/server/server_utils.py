import asyncio
import json
import os
import re
import traceback
from urllib.parse import quote
from typing import Awaitable, Dict, List, Any
from fastapi.responses import JSONResponse, FileResponse
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher import GPTResearcher
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
import logging

from gpt_researcher.utils.artifacts import (
    make_unique_artifact_stem,
    sanitize_filename as sanitize_artifact_filename,
)

try:
    from utils import write_md_to_pdf, write_md_to_word, write_text_to_md
except ImportError:  # pragma: no cover - package import fallback for tests.
    from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md

from .multi_agent_runner import run_multi_agent_task

# Import chat agent
try:
    import sys
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from chat.chat import ChatAgentWithMemory
except ImportError:
    ChatAgentWithMemory = None

logger = logging.getLogger(__name__)

class CustomLogsHandler:
    """Custom handler to capture streaming logs from the research process"""
    def __init__(self, websocket, task: str):
        self.logs = []
        self.websocket = websocket
        artifact_stem = make_unique_artifact_stem("task", task)
        self.log_file = os.path.join("outputs", f"{artifact_stem}.json")
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


class Researcher:
    def __init__(self, query: str, report_type: str = "research_report"):
        self.query = query
        self.report_type = report_type
        # Generate unique ID for this research task
        self.research_id = make_unique_artifact_stem("task", query)
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
        artifact_stem = make_unique_artifact_stem("task", self.query)
        verification_bundle = getattr(self.researcher, "verification_bundle", None)
        file_paths = await generate_report_files(
            report,
            artifact_stem,
            verification_bundle=verification_bundle,
        )
        
        # Get the JSON log path that was created by CustomLogsHandler
        json_relative_path = os.path.relpath(self.logs_handler.log_file)
        
        return {
            "output": {
                **file_paths,  # Include PDF, DOCX, and MD paths
                "json": json_relative_path
            }
        }

def sanitize_filename(filename: str) -> str:
    return sanitize_artifact_filename(filename)


# Windows reserved names
WINDOWS_RESERVED_NAMES = frozenset({
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
})


def secure_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValueError("Filename is empty")

    cleaned = filename.strip()
    cleaned = cleaned.replace("\x00", "")
    cleaned = re.sub(r"[\x01-\x1f\x7f]", "", cleaned)

    normalized = cleaned.replace("\\", "/")

    if re.search(r'(?:^|/)\.\.(?:/|$)', normalized):
        raise ValueError("Filename contains path traversal")

    parts = re.split(r'[/\\]+', cleaned)
    safe_parts = [p for p in parts if p and not all(c == '.' for c in p)]

    if not safe_parts:
        raise ValueError("Filename is empty")

    result = "".join(safe_parts)
    result = result.lstrip(". ")

    if len(result) >= 2 and result[1] == ':':
        result = result[2:]

    if not result:
        raise ValueError("Filename is empty")

    if len(result.encode('utf-8')) > 255:
        raise ValueError("Filename is too long")

    name_without_ext = result.rsplit('.', 1)[0].upper() if '.' in result else result.upper()
    base_name = name_without_ext.rstrip('.')
    if base_name in WINDOWS_RESERVED_NAMES:
        raise ValueError("Filename is a reserved name")

    return result


def validate_file_path(file_path: str, base_dir: str) -> str:
    abs_base = os.path.realpath(base_dir)
    abs_path = os.path.realpath(file_path)
    
    if not abs_path.startswith(abs_base + os.sep) and abs_path != abs_base:
        raise ValueError("File path is outside allowed directory")
    
    return abs_path


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
    ) = extract_command_data(json_data)

    if not task or not report_type:
        print("Fehler: task oder report_type fehlt")
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

    artifact_stem = make_unique_artifact_stem("task", task)

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
        max_search_results,
        logs_handler=logs_handler,
    )
    report = str(report)
    file_paths = await generate_report_files(report, artifact_stem)
    # Add JSON log path to file_paths
    file_paths["json"] = os.path.relpath(logs_handler.log_file)
    await send_file_paths(websocket, file_paths)


async def handle_human_feedback(data: str):
    feedback_data = json.loads(data[14:])  # Remove "human_feedback" prefix
    print(f"Erhaltenes menschliches Feedback: {feedback_data}")
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
                "content": "Keine Nachricht angegeben.",
                "role": "assistant"
            })
            return
        
        # Check if ChatAgentWithMemory is available
        if ChatAgentWithMemory is None:
            await websocket.send_json({
                "type": "chat",
                "content": "Chat-Funktionalität ist nicht verfügbar. Bitte prüfe die Serverkonfiguration.",
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
        logger.error(f"Chat-Daten konnten nicht geparst werden: {e}")
        await websocket.send_json({
            "type": "chat",
            "content": f"Fehler: Ungültiges Nachrichtenformat - {str(e)}",
            "role": "assistant"
        })
    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten des Chat-Befehls: {e}\n{traceback.format_exc()}")
        await websocket.send_json({
            "type": "chat",
            "content": f"Fehler bei der Verarbeitung deiner Nachricht: {str(e)}",
            "role": "assistant"
        })

async def write_verification_json(verification_bundle: dict[str, Any], filename: str) -> str:
    verification_path = os.path.join("outputs", f"{filename[:60]}.verification.json")
    os.makedirs("outputs", exist_ok=True)
    with open(verification_path, "w", encoding="utf-8") as handle:
        json.dump(verification_bundle, handle, indent=2, ensure_ascii=False)
    return quote(verification_path)


async def generate_report_files(
    report: str,
    filename: str,
    verification_bundle: dict[str, Any] | None = None,
) -> Dict[str, str]:
    pdf_path = await write_md_to_pdf(report, filename)
    docx_path = await write_md_to_word(report, filename)
    md_path = await write_text_to_md(report, filename)

    file_paths = {"pdf": pdf_path, "docx": docx_path, "md": md_path}
    if verification_bundle:
        file_paths["verification"] = await write_verification_json(verification_bundle, filename)

    return file_paths


async def send_file_paths(websocket, file_paths: Dict[str, str]):
    await websocket.send_json({"type": "path", "output": file_paths})


_CONFIG_DICT_KEYS = [
    "LANGCHAIN_API_KEY",
    "OPENAI_API_KEY",
    "TAVILY_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_CX_KEY",
    "BING_API_KEY",
    "SEARCHAPI_API_KEY",
    "SERPAPI_API_KEY",
    "SERPER_API_KEY",
    "SEARX_URL",
]

_STATIC_ENV_KEYS = {
    "LANGCHAIN_TRACING_V2": "true",
    "DOC_PATH": "./my-docs",
    "RETRIEVER": "duckduckgo",
    "EMBEDDING_MODEL": "",
}


def get_config_dict(**overrides: str) -> Dict[str, str]:
    result = {}
    for key in _CONFIG_DICT_KEYS:
        param_key = key.lower()
        result[key] = overrides.get(param_key) or os.getenv(key, "")
    for key, default in _STATIC_ENV_KEYS.items():
        result[key] = os.getenv(key, default)
    return result


def update_environment_variables(config: Dict[str, str]):
    for key, value in config.items():
        os.environ[key] = value


async def handle_file_upload(file, DOC_PATH: str) -> Dict[str, str]:
    try:
        safe_name = secure_filename(file.filename or "")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file name")
    
    os.makedirs(DOC_PATH, exist_ok=True)
    file_path = os.path.join(DOC_PATH, safe_name)
    
    if os.path.exists(file_path):
        base, ext = os.path.splitext(safe_name)
        counter = 1
        while os.path.exists(os.path.join(DOC_PATH, f"{base}_{counter}{ext}")):
            counter += 1
        safe_name = f"{base}_{counter}{ext}"
        file_path = os.path.join(DOC_PATH, safe_name)
    
    try:
        content = file.file.read()
        with open(file_path, "wb") as buffer:
            if isinstance(content, bytes):
                buffer.write(content)
            else:
                buffer.write(b"")
    except Exception:
        with open(file_path, "wb") as buffer:
            buffer.write(b"")
    print(f"Datei hochgeladen nach {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": safe_name, "path": file_path}


async def handle_file_deletion(filename: str, DOC_PATH: str) -> JSONResponse:
    try:
        safe_name = secure_filename(filename)
    except ValueError:
        return JSONResponse(status_code=400, content={"message": "Invalid file name"})
    
    file_path = os.path.join(DOC_PATH, safe_name)
    
    if os.path.isdir(file_path):
        return JSONResponse(status_code=400, content={"message": "Path is not a file"})
    
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Datei gelöscht: {file_path}")
        return JSONResponse(content={"message": "Datei erfolgreich gelöscht"})
    else:
        print(f"Datei nicht gefunden: {file_path}")
        return JSONResponse(status_code=404, content={"message": "Datei nicht gefunden"})


async def execute_multi_agents(manager) -> Any:
    websocket = manager.active_connections[0] if manager.active_connections else None
    if websocket:
        report = await run_multi_agent_task("Is AI in a hype cycle?", websocket, stream_output)
        return {"report": report}
    else:
        return JSONResponse(status_code=400, content={"message": "Keine aktive WebSocket-Verbindung"})


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
                logger.error(f"Fehler beim Ausführen der Aufgabe: {e}\n{traceback.format_exc()}")
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
                logger.info(f"Empfangene WebSocket-Nachricht: {data[:50]}..." if len(data) > 50 else data)
                
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
                            "output": "Aufgabe läuft bereits. Bitte warten.",
                        }
                    )
                # Normalize command detection by checking startswith after stripping whitespace
                elif data.strip().startswith("start"):
                    logger.info("Verarbeite Start-Befehl")
                    running_task = run_long_running_task(
                        handle_start_command(websocket, data, manager)
                    )
                elif data.strip().startswith("human_feedback"):
                    logger.info("Verarbeite human_feedback-Befehl")
                    running_task = run_long_running_task(handle_human_feedback(data))
                elif data.strip().startswith("chat"):
                    logger.info("Verarbeite Chat-Befehl")
                    running_task = run_long_running_task(handle_chat_command(websocket, data))
                else:
                    error_msg = f"Fehler: Unbekannter Befehl oder zu wenige Parameter. Empfangen: '{data[:100]}...'" if len(data) > 100 else f"Fehler: Unbekannter Befehl oder zu wenige Parameter. Empfangen: '{data}'"
                    logger.error(error_msg)
                    print(error_msg)
                    await websocket.send_json({
                        "type": "error",
                        "content": "error",
                        "output": "Unbekannter Befehl vom Server empfangen"
                    })
            except Exception as e:
                logger.error(f"WebSocket-Fehler: {str(e)}\n{traceback.format_exc()}")
                print(f"WebSocket-Fehler: {e}")
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
    )
