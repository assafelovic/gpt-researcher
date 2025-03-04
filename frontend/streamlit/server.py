"""
Streamlit server implementation for GPT Researcher.
This implementation is unified with the Next.js frontend to reduce code duplication.
It leverages the same chat functionality from backend/chat/chat.py that is used by the Next.js frontend.
"""

from __future__ import annotations

import argparse
import asyncio
import email.message
import email.parser
import email.policy
import http.server
import json
import logging
import mimetypes
import os
import re
import socketserver
import sys
import urllib.parse

from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, ClassVar

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

path = str(Path(__file__).absolute().parents[2])
if __name__ == "__main__" and path not in sys.path:
    sys.path.append(path)

from backend.chat.chat import ChatAgentWithMemory  # noqa: E402
from backend.server.server_utils import HTTPStreamAdapter, generate_report_files  # noqa: E402
from gpt_researcher.config import Config  # noqa: E402
from gpt_researcher.utils.enum import ReportFormat, ReportSource, ReportType, Tone  # noqa: E402

SCRIPT_DIR = Path(__file__).parent.absolute()

# Create necessary directories
for dir_path in ["logs", "outputs", "uploads"]:
    (SCRIPT_DIR / dir_path).mkdir(exist_ok=True, parents=True)


# Custom log handler that stores logs to be sent to the frontend
class FrontendLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_queue: asyncio.Queue = asyncio.Queue()
        self.formatter: logging.Formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")

    def emit(self, record):
        try:
            log_entry: str = self.format(record)
            level_name: str = str(record.levelname).lower()
            log_data: dict[str, Any] = {"type": "log", "level": level_name, "message": log_entry}

            # Add the log to the queue
            if not self.log_queue.full():
                asyncio.create_task(self._add_to_queue(json.dumps(log_data)))
        except Exception:
            self.handleError(record)

    async def _add_to_queue(
        self,
        log_data: str,
    ) -> None:
        """Helper method to add log data to the queue."""
        await self.log_queue.put(log_data)

    async def get_logs(self) -> list[str]:
        """Get all logs from the queue."""
        logs: list[str] = []
        while not self.log_queue.empty():
            try:
                log: str = await self.log_queue.get()
                logs.append(log)
                self.log_queue.task_done()
            except asyncio.QueueEmpty:
                break
        return logs


# Create the frontend log handler
frontend_log_handler = FrontendLogHandler()
frontend_log_handler.setLevel(logging.INFO)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(SCRIPT_DIR / "logs/backend_server.log")),
        logging.StreamHandler(),
        frontend_log_handler,  # Add the frontend log handler
    ],
)
logger = logging.getLogger(__name__)


def validate_config_file(content: bytes) -> bool:
    """Validate the uploaded config file.

    Args:
        content: The content of the config file.

    Returns:
        bool: True if the config file is valid, False otherwise.
    """
    try:
        # Try to parse the JSON
        config_dict = json.loads(content.decode("utf-8"))

        # Check if it's a dictionary
        if not isinstance(config_dict, dict):
            logger.error("Config file is not a dictionary")
            return False

        # Check if it has at least some expected keys
        expected_keys: list[str] = ["REPORT_TYPE", "REPORT_FORMAT", "LANGUAGE", "TONE"]
        if not any(key in config_dict for key in expected_keys):
            logger.error(f"Config file is missing expected keys: {expected_keys}")
            return False

        return True
    except json.JSONDecodeError as e:
        logger.exception(f"Invalid JSON in config file: {e.__class__.__name__}: {e}")
        return False
    except Exception as e:
        logger.exception(f"Error validating config file: {e.__class__.__name__}: {e}")
        return False


class ResearchAPIHandler:
    """Handler for research API requests."""

    # Store the latest report and chat agent for chat functionality
    _latest_report: ClassVar[str] = ""
    _chat_agent: ClassVar[ChatAgentWithMemory | None] = None

    @classmethod
    def set_latest_report(
        cls,
        report: str,
        config_path: str = "default",
    ) -> None:
        """Set the latest report and initialize a chat agent for it."""
        cls._latest_report = report
        cls._chat_agent = ChatAgentWithMemory(report, config_path)
        logger.info("Chat agent initialized with new report")

    @classmethod
    async def process_chat_message(
        cls,
        message: str,
    ) -> str:
        """Process a chat message and return the response as a JSON string.

        This method uses the ChatAgentWithMemory directly instead of WebSocketManager
        to align with the Next.js implementation.
        """
        try:
            if not cls._chat_agent or not cls._latest_report:
                return json.dumps(
                    {
                        "type": "chat",
                        "content": "Knowledge empty, please run the research first to obtain knowledge",
                    }
                )

            # Create an adapter for the response
            message_queue: asyncio.Queue = asyncio.Queue()
            http_adapter: HTTPStreamAdapter = HTTPStreamAdapter(message_queue)

            # Use the chat agent directly
            response: str = await cls._chat_agent.chat(message, http_adapter)

            # Format the response as JSON
            return json.dumps(
                {
                    "type": "chat",
                    "content": response,
                }
            )

        except Exception as e:
            logger.exception(f"Error in chat process! {e.__class__.__name__}: {e}")
            return json.dumps({"type": "error", "content": f"Error in chat process! {e.__class__.__name__}: {e}"})

    @staticmethod
    async def stream_research(
        params: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Stream the research process with progress updates"""
        try:
            from backend.server.websocket_manager import WebSocketManager  # noqa: E402

            manager: WebSocketManager = WebSocketManager()
            message_queue: asyncio.Queue = asyncio.Queue()
            http_adapter: HTTPStreamAdapter = HTTPStreamAdapter(message_queue)
            await manager.connect(http_adapter)

            task: str = params.get("query", "")
            report_type: str = params.get("report_type", "")

            source_urls: list[str] = str(params.get("source_urls", "")).split(",") if params.get("source_urls") else []
            query_domains: list[str] = str(params.get("query_domains", "")).split(",") if params.get("query_domains") else []

            # Load config from the config.json file
            config_path: Path = SCRIPT_DIR / "config.json"
            if config_path.exists():
                config: Config = Config.from_path(config_path)
                logger.info(f"Using config from '{config_path}'")
            else:
                # Create a default config if the file doesn't exist
                config = Config()
                logger.info("Using default config")
                # Save the default config for future use
                config_path.write_text(config.to_json())
                logger.info(f"Default config saved to '{config_path}'")

            # Update config with form parameters
            config.CURATE_SOURCES = str(params.get("curate_sources", config.CURATE_SOURCES)).lower() == "true"
            config.EMBEDDING_KWARGS = (
                json.loads(params.get("embedding_kwargs", json.dumps(config.EMBEDDING_KWARGS))) or config.EMBEDDING_KWARGS
            )
            config.EMBEDDING_MODEL = params.get("embedding_model", config.EMBEDDING_MODEL) or config.EMBEDDING_MODEL
            config.EMBEDDING_PROVIDER = (
                params.get("embedding_provider", config.EMBEDDING_PROVIDER) or config.EMBEDDING_PROVIDER
            )
            config.EMBEDDING = params.get("embedding", config.EMBEDDING) or config.EMBEDDING
            config.FALLBACK_MODELS = (
                str(params.get("fallback_models", "")).split(",")
                if params.get("fallback_models")
                else config.FALLBACK_MODELS
            )
            config.FAST_LLM_MODEL = params.get("fast_llm_model", config.FAST_LLM_MODEL) or config.FAST_LLM_MODEL
            config.FAST_LLM_PROVIDER = params.get("fast_llm_provider", config.FAST_LLM_PROVIDER) or config.FAST_LLM_PROVIDER
            config.FAST_LLM = params.get("fast_llm", config.FAST_LLM) or config.FAST_LLM
            config.FAST_TOKEN_LIMIT = int(params.get("fast_token_limit", config.FAST_TOKEN_LIMIT)) or config.FAST_TOKEN_LIMIT
            config.LANGUAGE = params.get("language", config.LANGUAGE) or config.LANGUAGE
            config.MAX_ITERATIONS = int(params.get("max_iterations", config.MAX_ITERATIONS)) or config.MAX_ITERATIONS
            config.MAX_SEARCH_RESULTS_PER_QUERY = (
                int(params.get("max_search_results_per_query", config.MAX_SEARCH_RESULTS_PER_QUERY))
                or config.MAX_SEARCH_RESULTS_PER_QUERY
            )
            config.MAX_SUBTOPICS = int(params.get("max_subtopics", config.MAX_SUBTOPICS)) or config.MAX_SUBTOPICS
            config.MEMORY_BACKEND = ReportSource(
                str(params.get("memory_backend", config.MEMORY_BACKEND.value)) or config.MEMORY_BACKEND.value
            )
            config.REPORT_FORMAT = ReportFormat.__members__[
                str(params.get("report_format", config.REPORT_FORMAT.name)).upper() or config.REPORT_FORMAT.name
            ]
            config.REPORT_SOURCE = ReportSource(
                str(params.get("report_source", config.REPORT_SOURCE.value) or config.REPORT_SOURCE.value).casefold()
            )
            report_type = str(params.get("report_type", config.REPORT_TYPE.name)) or config.REPORT_TYPE.name
            if report_type not in ReportType.__members__:
                report_type = report_type.replace("_", " ").title().replace(" ", "")
            config.REPORT_TYPE = ReportType.__members__[report_type]
            config.RESEARCH_PLANNER = params.get("research_planner", config.RESEARCH_PLANNER) or config.RESEARCH_PLANNER
            config.RETRIEVER = params.get("retriever", config.RETRIEVER) or config.RETRIEVER
            config.SCRAPER = params.get("scraper", config.SCRAPER) or config.SCRAPER
            config.SIMILARITY_THRESHOLD = (
                float(params.get("similarity_threshold", config.SIMILARITY_THRESHOLD)) or config.SIMILARITY_THRESHOLD
            )
            config.SMART_LLM_MODEL = params.get("smart_llm_model", config.SMART_LLM_MODEL) or config.SMART_LLM_MODEL
            config.SMART_LLM_PROVIDER = (
                params.get("smart_llm_provider", config.SMART_LLM_PROVIDER) or config.SMART_LLM_PROVIDER
            )
            config.SMART_LLM = params.get("smart_llm", config.SMART_LLM) or config.SMART_LLM
            config.SMART_TOKEN_LIMIT = (
                int(params.get("smart_token_limit", config.SMART_TOKEN_LIMIT)) or config.SMART_TOKEN_LIMIT
            )
            config.STRATEGIC_LLM_MODEL = (
                params.get("strategic_llm_model", config.STRATEGIC_LLM_MODEL) or config.STRATEGIC_LLM_MODEL
            )
            config.STRATEGIC_LLM_PROVIDER = (
                params.get("strategic_llm_provider", config.STRATEGIC_LLM_PROVIDER) or config.STRATEGIC_LLM_PROVIDER
            )
            config.STRATEGIC_LLM = params.get("strategic_llm", config.STRATEGIC_LLM) or config.STRATEGIC_LLM
            config.STRATEGIC_TOKEN_LIMIT = (
                params.get("strategic_token_limit", config.STRATEGIC_TOKEN_LIMIT) or config.STRATEGIC_TOKEN_LIMIT
            )
            config.TEMPERATURE = float(params.get("temperature", config.TEMPERATURE)) or config.TEMPERATURE
            config.TONE = (
                Tone.__members__[str(params.get("tone", config.TONE.name) or config.TONE.name).capitalize()] or config.TONE
            )
            config.TOTAL_WORDS = int(params.get("total_words", config.TOTAL_WORDS) or config.TOTAL_WORDS)
            config.USE_FALLBACKS = (
                str(params.get("use_fallbacks", config.USE_FALLBACKS) or config.USE_FALLBACKS).lower() == "true"
            )
            config.USER_AGENT = params.get("user_agent", config.USER_AGENT) or config.USER_AGENT
            config.VERBOSE = str(params.get("verbose", config.VERBOSE)).lower() == "true" or config.VERBOSE

            # Add missing variables from Config
            config.AGENT_ROLE = params.get("agent_role", config.AGENT_ROLE) or config.AGENT_ROLE
            config.DOC_PATH = params.get("doc_path", config.DOC_PATH) or config.DOC_PATH
            config.EMBEDDING_FALLBACK_MODELS = (
                str(params.get("embedding_fallback_models", "")).split(",")
                if params.get("embedding_fallback_models")
                else config.EMBEDDING_FALLBACK_MODELS
            )
            config.FAST_LLM_TEMPERATURE = (
                float(params.get("fast_llm_temperature", config.FAST_LLM_TEMPERATURE)) or config.FAST_LLM_TEMPERATURE
            )
            config.MAX_URLS = int(params.get("max_urls", config.MAX_URLS)) or config.MAX_URLS
            config.OUTPUT_FORMAT = params.get("output_format", config.OUTPUT_FORMAT) or config.OUTPUT_FORMAT
            config.SMART_LLM_TEMPERATURE = (
                float(params.get("smart_llm_temperature", config.SMART_LLM_TEMPERATURE)) or config.SMART_LLM_TEMPERATURE
            )
            config.STRATEGIC_LLM_TEMPERATURE = (
                float(params.get("strategic_llm_temperature", config.STRATEGIC_LLM_TEMPERATURE))
                or config.STRATEGIC_LLM_TEMPERATURE
            )
            config.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS = (
                params.get("post_retrieval_processing_instructions", config.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS)
                or config.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS
            )
            config.PROMPT_GENERATE_SEARCH_QUERIES = (
                params.get("prompt_generate_search_queries", config.PROMPT_GENERATE_SEARCH_QUERIES)
                or config.PROMPT_GENERATE_SEARCH_QUERIES
            )
            config.PROMPT_GENERATE_REPORT = (
                params.get("prompt_generate_report", config.PROMPT_GENERATE_REPORT) or config.PROMPT_GENERATE_REPORT
            )
            config.PROMPT_CURATE_SOURCES = (
                params.get("prompt_curate_sources", config.PROMPT_CURATE_SOURCES) or config.PROMPT_CURATE_SOURCES
            )
            config.PROMPT_GENERATE_RESOURCE_REPORT = (
                params.get("prompt_generate_resource_report", config.PROMPT_GENERATE_RESOURCE_REPORT)
                or config.PROMPT_GENERATE_RESOURCE_REPORT
            )
            config.PROMPT_GENERATE_CUSTOM_REPORT = (
                params.get("prompt_generate_custom_report", config.PROMPT_GENERATE_CUSTOM_REPORT)
                or config.PROMPT_GENERATE_CUSTOM_REPORT
            )
            config.PROMPT_GENERATE_OUTLINE_REPORT = (
                params.get("prompt_generate_outline_report", config.PROMPT_GENERATE_OUTLINE_REPORT)
                or config.PROMPT_GENERATE_OUTLINE_REPORT
            )
            config.PROMPT_AUTO_AGENT_INSTRUCTIONS = (
                params.get("prompt_auto_agent_instructions", config.PROMPT_AUTO_AGENT_INSTRUCTIONS)
                or config.PROMPT_AUTO_AGENT_INSTRUCTIONS
            )
            config.PROMPT_CONDENSE_INFORMATION = (
                params.get("prompt_condense_information", config.PROMPT_CONDENSE_INFORMATION)
                or config.PROMPT_CONDENSE_INFORMATION
            )
            config.PROMPT_GENERATE_SUBTOPICS = (
                params.get("prompt_generate_subtopics", config.PROMPT_GENERATE_SUBTOPICS) or config.PROMPT_GENERATE_SUBTOPICS
            )
            config.PROMPT_GENERATE_SUBTOPIC_REPORT = (
                params.get("prompt_generate_subtopic_report", config.PROMPT_GENERATE_SUBTOPIC_REPORT)
                or config.PROMPT_GENERATE_SUBTOPIC_REPORT
            )
            config.PROMPT_GENERATE_DRAFT_TITLES = (
                params.get("prompt_generate_draft_titles", config.PROMPT_GENERATE_DRAFT_TITLES)
                or config.PROMPT_GENERATE_DRAFT_TITLES
            )
            config.PROMPT_GENERATE_REPORT_INTRODUCTION = (
                params.get("prompt_generate_report_introduction", config.PROMPT_GENERATE_REPORT_INTRODUCTION)
                or config.PROMPT_GENERATE_REPORT_INTRODUCTION
            )
            config.PROMPT_GENERATE_REPORT_CONCLUSION = (
                params.get("prompt_generate_report_conclusion", config.PROMPT_GENERATE_REPORT_CONCLUSION)
                or config.PROMPT_GENERATE_REPORT_CONCLUSION
            )
            config.PROMPT_POST_RETRIEVAL_PROCESSING = (
                params.get("prompt_post_retrieval_processing", config.PROMPT_POST_RETRIEVAL_PROCESSING)
                or config.PROMPT_POST_RETRIEVAL_PROCESSING
            )

            config_path.write_text(config.to_json())

            yield "Starting research process...\n"
            yield f"Query: {task}\n"
            yield f"Report Type: {report_type}\n"

            if query_domains:
                yield f"Searching in domains: {', '.join(query_domains)}\n"

            # Start a background task to forward logs to the client
            async def forward_logs() -> None:
                while True:
                    logs: list[str] = await frontend_log_handler.get_logs()
                    for log in logs:
                        await message_queue.put(f"data: {log}\n\n")
                    await asyncio.sleep(0.5)  # Check for new logs every 0.5 seconds

            # Create the log forwarding task
            log_task: asyncio.Task = asyncio.create_task(forward_logs())

            try:
                report: str = await manager.start_streaming(
                    task=task,
                    report_type=report_type,
                    report_source=config.REPORT_SOURCE.value,
                    source_urls=source_urls or [],
                    document_urls=params.get("document_urls", []),
                    tone=config.TONE,
                    websocket=http_adapter,
                    query_domains=query_domains,
                )

                # Store the report for chat functionality
                ResearchAPIHandler.set_latest_report(report, str(config_path))

                sanitized_filename: str = task.replace(" ", "_")[:50]
                timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_filename: str = f"task_{timestamp}_{sanitized_filename}"

                file_paths: dict[str, Path] = await generate_report_files(report, base_filename)

                while not message_queue.empty():
                    try:
                        message: str = message_queue.get_nowait()
                        yield message + "\n"
                    except asyncio.QueueEmpty:
                        break

                yield "\nResearch complete.\n"
                yield "-------------------\n"

                for fmt in ["md", "pdf", "docx"]:
                    yield f"data: {json.dumps({'type': 'file_ready', 'format': fmt})}\n\n"

                files: dict[str, str] = {fmt: f"/outputs/{os.path.basename(path)}" for fmt, path in file_paths.items()}

                files_ready_info: dict[str, Any] = {
                    "type": "files_ready",
                    "message": "All output files have been generated.",
                    "files": files,
                }
                yield f"data: {json.dumps(files_ready_info)}\n\n"

                report_info: dict[str, Any] = {
                    "type": "report_complete",
                    "content": report,
                    "query": task,
                    "timestamp": timestamp,
                    "base_filename": base_filename,
                    "files": files,
                }
                yield f"data: {json.dumps(report_info)}\n\n"
            finally:
                # Cancel the log forwarding task
                log_task.cancel()
                try:
                    await log_task
                except asyncio.CancelledError:
                    pass

            await manager.disconnect(http_adapter)

        except Exception as e:
            logger.exception(f"Error in research stream! {e.__class__.__name__}: {e}")
            yield f"\nError in research stream! {e.__class__.__name__}: {e}\n"
            raise

    @staticmethod
    def get_default_prompt_templates() -> dict[str, str]:
        """Get default prompt templates from the Config class."""
        default_config: dict[str, Any] = Config.default_config_dict()
        return {k: v for k, v in default_config.items() if k.startswith("PROMPT_")}

    @staticmethod
    def save_config_file(content: bytes) -> bool:
        """Save a config file if it's valid.

        Args:
        ----
            content: The content of the config file.

        Returns:
        -------
            bool: True if the config file was saved successfully, False otherwise.
        """
        if validate_config_file(content):
            try:
                # Save the config file
                config_path = SCRIPT_DIR / "config.json"
                config_path.write_bytes(content)
                logger.info(f"Uploaded config file saved to '{config_path}'")
                return True
            except Exception as e:
                logger.exception(f"Error saving config file! {e.__class__.__name__}: {e}")
                return False
        else:
            logger.error(f"Invalid config file: {content.decode()}")
            return False

    @staticmethod
    def save_uploaded_file(
        filename: str,
        content: bytes,
    ) -> str:
        """Save an uploaded file.

        Args:
        ----
            filename: The name of the file.
            content: The content of the file.

        Returns:
        -------
            str: The path to the saved file.
        """
        file_path: Path = SCRIPT_DIR / "uploads" / filename
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.write_bytes(content)
        return str(file_path)

    @staticmethod
    def get_file_content(file_path: os.PathLike | str) -> tuple[bytes, int, str]:
        """Get the content of a file.

        Args:
        ----
            file_path: The path to the file.

        Returns:
        -------
            tuple: The file content, size, and content type.
        """
        path: Path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: '{file_path}'")

        file_size = path.stat().st_size
        data = path.read_bytes()

        ext = os.path.splitext(path)[1]
        content_type = mimetypes.guess_type(path)[0]
        if not content_type and ext in mimetypes.types_map:
            content_type = mimetypes.types_map[ext]
        if not content_type:
            content_type = "application/octet-stream"

        return data, file_size, content_type


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(SCRIPT_DIR / "logs/frontend_server.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Initialize MIME types
mimetypes.init()
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/html", ".html")

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(SCRIPT_DIR / "static/templates"), autoescape=True)


class AsyncStreamingResearchRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.jinja_env = Environment(
            loader=FileSystemLoader(SCRIPT_DIR / "static/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests - serve static files and the HTML form"""
        parsed_path: urllib.parse.ParseResult = urllib.parse.urlparse(self.path)
        path: str = parsed_path.path

        # Serve Next.js chat icons to unify the UI
        if path == "/img/chat.svg" or path == "/img/chat-check.svg":
            try:
                # Define the path to the Next.js assets
                nextjs_asset_path: Path = Path(__file__).absolute().parents[2] / "frontend" / "nextjs" / "public" / path[1:]

                if not nextjs_asset_path.exists():
                    self.send_error(404, "File not found")
                    return

                # Get file content
                data = nextjs_asset_path.read_bytes()
                file_size = nextjs_asset_path.stat().st_size
                content_type = "image/svg+xml"

                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.send_header("Content-Length", str(file_size))
                self.end_headers()

                self.wfile.write(data)
                return
            except Exception as e:
                logger.exception(f"Error serving Next.js asset: {e.__class__.__name__}: {e}")
                self.send_error(500, f"Internal server error! {e.__class__.__name__}: {e}")
                return

        if path == "/":
            # Load default config
            config_path: Path = SCRIPT_DIR / "config.json"
            try:
                config = Config.from_path(config_path)
            except Exception as e:
                logger.exception(f"Error loading config! {e.__class__.__name__}: {e}")
                config = Config()

            config_path.write_text(config.to_json())

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            report_types: dict[str, str] = {
                "research_report": ReportType.ResearchReport.value,
                "detailed_report": ReportType.DetailedReport.value,
                "multi_agents": ReportType.MultiAgents.value,
                #                "resource_report": ReportType.ResourceReport.value,
                #                "outline_report": ReportType.OutlineReport.value,
                #                "custom_report": ReportType.CustomReport.value,
                #                "subtopic_report": ReportType.SubtopicReport.value,
                #                "draft_titles": ReportType.DraftTitles.value,
            }

            report_formats: dict[str, str] = {rf.name.lower(): rf.name.upper() for rf in ReportFormat.__members__.values()}

            report_sources: dict[str, str] = {
                ReportSource.Web.name.capitalize(): ReportSource.Web.value,
                ReportSource.Local.name.capitalize(): ReportSource.Local.value,
                ReportSource.Hybrid.name.capitalize(): ReportSource.Hybrid.value,
                #                ReportSource.Azure.name.capitalize(): ReportSource.Azure.value,
                #                "langchain_documents": ReportSource.LangChainDocuments.value,
                #                "langchain_vectorstore": ReportSource.LangChainVectorStore.value,
                #                ReportSource.Static.name.capitalize(): ReportSource.Static.value,
            }

            tones: dict[str, str] = {
                Tone.Objective.name.lower(): Tone.Objective.value,
                Tone.Formal.name.lower(): Tone.Formal.value,
                Tone.Analytical.name.lower(): Tone.Analytical.value,
                Tone.Informative.name.lower(): Tone.Informative.value,
                Tone.Descriptive.name.lower(): Tone.Descriptive.value,
                Tone.Persuasive.name.lower(): Tone.Persuasive.value,
                Tone.Critical.name.lower(): Tone.Critical.value,
                Tone.Comparative.name.lower(): Tone.Comparative.value,
                Tone.Speculative.name.lower(): Tone.Speculative.value,
                Tone.Reflective.name.lower(): Tone.Reflective.value,
                Tone.Narrative.name.lower(): Tone.Narrative.value,
                Tone.Humorous.name.lower(): Tone.Humorous.value,
                Tone.Optimistic.name.lower(): Tone.Optimistic.value,
                Tone.Pessimistic.name.lower(): Tone.Pessimistic.value,
            }

            html = self.jinja_env.get_template("index.html").render(
                config=config,
                report_types=report_types,
                report_formats=report_formats,
                report_sources=report_sources,
                tones=tones,
            )
            self.wfile.write(html.encode())
            return

        # Add API endpoint for getting default prompt templates
        elif self.path == "/api/prompt-defaults":
            try:
                # Get default prompt templates from the backend
                prompt_defaults: dict[str, str] = ResearchAPIHandler.get_default_prompt_templates()

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(prompt_defaults).encode())
                return
            except Exception as e:
                logger.exception(f"Error getting default prompt templates! {e.__class__.__name__}: {e}")
                self.send_error(500, "Internal server error")
                return

        if self.path.startswith("/static/") or self.path.startswith("/outputs/"):
            try:
                file: str = self.path[1:]
                file_path: Path = SCRIPT_DIR / file

                if not file_path.exists():
                    self.send_error(404, "File not found")
                    return

                try:
                    # Use the backend to get file content
                    data, file_size, content_type = ResearchAPIHandler.get_file_content(str(file_path))
                except FileNotFoundError:
                    self.send_error(404, "File not found")
                    return

                self.send_response(200)

                if self.path.startswith("/outputs/"):
                    filename = os.path.basename(file_path)
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')

                self.send_header("Content-type", content_type)
                self.send_header("Content-Length", str(file_size))
                self.end_headers()

                chunk_size = 8192
                for i in range(0, len(data), chunk_size):
                    chunk = data[i : i + chunk_size]
                    self.wfile.write(chunk)
                    self.wfile.flush()

            except Exception as e:
                logger.exception(f"Error serving static file! {e.__class__.__name__}: {e}")
                self.send_error(500, f"Internal server error! {e.__class__.__name__}: {e}")
            return

        if self.path.startswith("/research"):
            parsed_url: urllib.parse.ParseResult = urllib.parse.urlparse(self.path)
            params: dict[str, Any] = dict(urllib.parse.parse_qsl(parsed_url.query))

            if not params.get("query") or not params.get("report_type"):
                self.send_error(400, "Missing required parameters: query and report_type")
                return

            try:
                self.send_response(200)
                self.send_header("Content-type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()

                loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def stream() -> None:
                    async for chunk in ResearchAPIHandler.stream_research(params):
                        self.wfile.write(chunk.encode())
                        self.wfile.flush()

                loop.run_until_complete(stream())
                loop.close()

            except Exception as e:
                logger.exception(f"Error conducting research! {e.__class__.__name__}: {e}")
                error_msg: str = json.dumps({"error": f"{e.__class__.__name__}: {e}"})
                self.wfile.write(f"data: {error_msg}\n\n".encode())
                self.wfile.flush()
                return
        else:
            self.send_error(404, "Not found")
            return

    def do_POST(self) -> None:
        """Handle POST requests - process file uploads and research requests"""
        try:
            logger.info(f"Received POST request to {self.path}")
            parsed_path: urllib.parse.ParseResult = urllib.parse.urlparse(self.path)
            path: str = parsed_path.path
            query: dict[str, Any] = urllib.parse.parse_qs(parsed_path.query)

            logger.info(f"POST path: {path}, query: {query}")
            logger.info(f"Headers: {self.headers}")

            if path == "/research":
                logger.info("Handling research request")
                self._handle_research_request(query)
            elif path == "/chat":
                logger.info("Handling chat request")
                self._handle_chat_request()
            elif path == "/load_config":
                logger.info("Handling load config request")
                self._handle_load_config_request()
            else:
                logger.warning(f"Unknown POST path: '{path}'")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")
        except Exception as e:
            logger.exception(f"Error handling request! {e.__class__.__name__}: {e}")
            self.send_error(500, f"Internal server error! {e.__class__.__name__}: {e}")

    def _handle_load_config_request(self):
        """Handle loading config from JSON."""
        content_length: int = int(self.headers["Content-Length"])
        post_data: str = self.rfile.read(content_length).decode("utf-8")

        try:
            config_data: dict[str, Any] = json.loads(post_data)
            config: Config = Config.from_dict(config_data)

            # Save the config
            config_path: Path = SCRIPT_DIR / "config.json"
            config_path.write_text(config.to_json())

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response: dict[str, Any] = {
                "status": "success",
                "message": "Configuration loaded successfully",
                "config": config.to_dict(),
            }
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response = {
                "status": "error",
                "message": f"Error loading configuration! {e.__class__.__name__}: {e}",
            }
            self.wfile.write(json.dumps(response).encode())

    def _handle_research_request(
        self,
        query: dict[str, Any] | None = None,
    ) -> None:
        """Handle research request."""
        try:
            # Parse the form data using email.parser instead of cgi.FieldStorage
            content_type: str = str(self.headers.get("Content-Type", "")).strip()
            logger.info(f"Received research request with Content-Type: {content_type}")

            if not content_type.startswith("multipart/form-data"):
                logger.error(f"Invalid 'Content-Type': '{content_type}', expected 'multipart/form-data'")
                self.send_error(400, "Expected 'multipart/form-data'")
                return

            # Get content length
            content_length: int = int(self.headers.get("Content-Length", 0))

            # Read the entire form data
            form_data: bytes = self.rfile.read(content_length)

            # Get boundary from content type
            boundary: str | None = None
            for part in content_type.split(";"):
                part: str = part.strip()
                if part.startswith("boundary="):
                    boundary = part[9:]
                    if boundary.startswith('"') and boundary.endswith('"'):
                        boundary = boundary[1:-1]
                    break

            if not boundary:
                logger.error("No boundary found in 'Content-Type' header")
                self.send_error(400, "Invalid 'multipart/form-data': no boundary")
                return

            # Prepare the message with appropriate headers for the parser
            message_text: str = f"Content-Type: {content_type}\r\n\r\n"
            message_bytes: bytes = message_text.encode("utf-8") + form_data

            # Parse the multipart form data
            parser = email.parser.BytesParser(policy=email.policy.HTTP)
            multipart_data: email.message.Message[str, str] = parser.parsebytes(message_bytes)

            # Ensure we're working with a multipart message
            if not multipart_data.is_multipart():
                logger.error("Parsed data is not multipart")
                self.send_error(400, "Invalid 'multipart/form-data' format")
                return

            # Process the form data
            params: dict[str, Any] = {}
            document_paths: list[str] = []

            # Get all parts of the multipart message
            parts = multipart_data.get_payload()
            logger.info(f"Parsing form with {len(parts)} parts")

            # Process each part in the multipart data
            for p in parts:
                # Ensure part is an email.message.EmailMessage
                if not isinstance(p, email.message.EmailMessage):
                    continue

                # Get the field name from Content-Disposition
                content_disposition: str = p.get("Content-Disposition", "")
                field_name_match: re.Match | None = re.search(r'name="([^"]*)"', content_disposition)
                if not field_name_match:
                    continue

                field_name = field_name_match.group(1)

                # Check if this is a file upload
                filename_match: re.Match | None = re.search(r'filename="([^"]*)"', content_disposition)

                if filename_match and filename_match.group(1):
                    # This is a file upload
                    filename: str = filename_match.group(1)
                    if not filename:
                        continue

                    logger.info(f"Processing file upload: {filename}")

                    # Get the file content
                    content_payload = p.get_payload(decode=True)
                    # Ensure content is bytes
                    if isinstance(content_payload, bytes):
                        content = content_payload
                    else:
                        content = bytes(str(content_payload), "utf-8")

                    logger.info(f"Received file: {filename} ({len(content)} bytes)")

                    # Handle config file upload
                    if field_name == "config_file" and str(filename).casefold().endswith(".json"):
                        ResearchAPIHandler.save_config_file(content)
                    else:
                        # Handle regular file uploads
                        file_path: str = ResearchAPIHandler.save_uploaded_file(filename, content)
                        document_paths.append(file_path)
                else:
                    # This is a regular form field
                    payload = p.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        charset = p.get_content_charset("utf-8")
                        value_str = payload.decode(charset)
                    else:
                        value_str = str(payload)

                    value_str = value_str.strip()
                    logger.info(f"Received form field: {field_name}={value_str}")

                    # Handle prompt environment variables
                    if str(field_name).startswith("PROMPT_"):
                        # Only set environment variables if they have a value
                        if value_str:
                            os.environ[field_name] = value_str
                            logger.info(f"Set environment variable '{field_name}'")
                        # If empty, remove from environment to use default
                        elif field_name in os.environ:
                            del os.environ[field_name]
                            logger.info(f"Removed environment variable '{field_name}'")
                    else:
                        params[field_name] = value_str

            # Add document paths to params
            params["document_urls"] = document_paths

            logger.info(f"Finished parsing form data. Found {len(parts)} parts.")
            logger.info(f"Params: {params}")

            # Check required parameters
            if not params.get("query", query) or not params.get("report_type"):
                logger.error(f"Missing required parameters. Params: {params}")
                self.send_error(400, "Missing required parameters: `query` and `report_type`")
                return

            logger.info(f"Starting research with parameters: {params}")

            self.send_response(200)
            self.send_header("Content-type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def stream() -> None:
                try:
                    logger.info("Starting research stream")
                    async for chunk in ResearchAPIHandler.stream_research(params):
                        self.wfile.write(chunk.encode())
                        self.wfile.flush()
                    logger.info("Research stream completed")
                except Exception as e:
                    logger.exception(f"Error in research stream! {e.__class__.__name__}: {e}")
                    error_msg: str = f"Error in research stream! {e.__class__.__name__}: {e}"
                    self.wfile.write(error_msg.encode())
                    self.wfile.flush()

            loop.run_until_complete(stream())
            loop.close()

        except Exception as e:
            logger.exception(f"Error handling POST request! {e.__class__.__name__}: {e}")
            self.send_error(500, f"Internal server error!    {e.__class__.__name__}: {e}")
            return

    def _handle_chat_request(self):
        """Handle chat request."""
        try:
            # Get content length as an integer
            content_length_str: str = self.headers.get("Content-Length", "0")
            content_length: int = int(content_length_str)

            # Read the request body
            body_bytes: bytes = self.rfile.read(content_length)
            body: str = body_bytes.decode("utf-8")

            # Parse JSON data
            data: dict[str, Any] = json.loads(body)
            message: str = data.get("message", "")

            if not message or not message.strip():
                self.send_error(400, "Message is required and cannot be empty")
                return

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            # Process the chat message using the ChatAgentWithMemory directly
            loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_text: str = loop.run_until_complete(ResearchAPIHandler.process_chat_message(message))
            loop.close()

            self.wfile.write(response_text.encode("utf-8"))
            return
        except Exception as e:
            logger.exception(f"Error handling chat request! {e.__class__.__name__}: {e}")
            self.send_error(500, f"Internal server error! {e.__class__.__name__}: {e}")
            return


def run_server(
    host: str = "0.0.0.0",
    port: int = 8080,
) -> None:
    """Run the web server on the specified port"""
    load_dotenv()

    class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    with ThreadingHTTPServer((host, port), AsyncStreamingResearchRequestHandler) as httpd:
        logger.info(f"Server started at 'http://{host}:{port}'")
        logger.info("Using threaded server that can handle multiple concurrent connections")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            httpd.server_close()


path = str(Path(__file__).absolute().parents[2])
if __name__ == "__main__" and path not in sys.path:
    sys.path.append(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the GPT Researcher web server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on (default: 8080)")
    args: argparse.Namespace = parser.parse_args()
    run_server(port=args.port)
