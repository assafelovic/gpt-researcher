from __future__ import annotations

import argparse
import asyncio
import http.server
import json
import logging
import mimetypes
import os
import socketserver
import sys
import urllib.parse

from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, Template

path = str(Path(__file__).absolute().parents[2])
if __name__ == "__main__" and path not in sys.path:
    sys.path.append(path)

from backend.server.server_utils import HTTPStreamAdapter, generate_report_files  # noqa: E402
from backend.server.websocket_manager import WebSocketManager  # noqa: E402
from gpt_researcher.config import Config  # noqa: E402
from gpt_researcher.utils.enum import ReportFormat, ReportSource, ReportType, Tone  # noqa: E402

SCRIPT_DIR = Path(__file__).parent.absolute()


for dir_path in ["logs", "outputs"]:
    (SCRIPT_DIR / dir_path).mkdir(exist_ok=True, parents=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(SCRIPT_DIR / "logs/webserver.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


mimetypes.init()
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/html", ".html")


env = Environment(loader=FileSystemLoader(SCRIPT_DIR / "static/templates"), autoescape=True)


class AsyncStreamingResearchRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        """Handle GET requests - serve static files and the HTML form"""
        if self.path == "/":
            self.path = "/static/templates/index.html"
            try:
                config_path: Path = SCRIPT_DIR / "config.json"
                config: Config = Config.from_path(config_path)

                template: Template = env.get_template("index.html")

                context: dict[str, Any] = {
                    "config": config,
                    "report_types": {
                        "ResearchReport": "Quick Summary (~2 min)",
                        "DetailedReport": "Detailed Analysis (~5 min)",
                        "MultiAgents": "Multi-Agent Report",
                        # none of these are user interactable.
                        #                        "ResourceReport": "Resource Report",
                        #                        "OutlineReport": "Outline Report",
                        #                        "CustomReport": "Custom Report",
                        #                        "SubtopicReport": "Subtopic Report",
                    },
                    "report_formats": {
                        "APA": "APA Style",
                        "MLA": "MLA Style",
                        "Chicago": "Chicago Style",
                        "Harvard": "Harvard Style",
                        "Vancouver": "Vancouver Style",
                        "IEEE": "IEEE Style",
                        "AMA": "AMA Style",
                        "CSE": "CSE Style",
                        "ASA": "ASA Style",
                        "AIP": "AIP Style",
                        "APSA": "APSA Style",
                        "Bluebook": "Bluebook Style",
                        "Chicago17": "Chicago17 Style",
                        "MLA8": "MLA8 Style",
                        "MLA9": "MLA9 Style",
                        "NLM": "NLM Style",
                        "OSCOLA": "OSCOLA Style",
                        "IEEETRAN": "IEEETRAN Style",
                        "AAG": "AAG Style",
                        "SBL": "SBL Style",
                        "Turabian": "Turabian Style",
                    },
                    "report_sources": {
                        "web": "Web Sources",
                        "local": "Local Documents",
                        "all": "All Sources",
                    },
                    "tones": {
                        "Objective": "Objective (impartial and unbiased presentation of facts and findings)",
                        "Formal": "Formal (adheres to academic standards with sophisticated language and structure)",
                        "Analytical": "Analytical (critical evaluation and detailed examination of data and theories)",
                        "Persuasive": "Persuasive (convincing the audience of a particular viewpoint or argument)",
                        "Informative": "Informative (providing clear and comprehensive information on a topic)",
                        "Explanatory": "Explanatory (clarifying complex concepts and processes)",
                        "Descriptive": "Descriptive (detailed depiction of phenomena, experiments, or case studies)",
                        "Critical": "Critical (judging the validity and relevance of the research and its conclusions)",
                        "Comparative": "Comparative (juxtaposing different theories, data, or methods)",
                        "Speculative": "Speculative (exploring hypotheses and potential implications)",
                        "Reflective": "Reflective (considering the research process and personal insights)",
                        "Narrative": "Narrative (telling a story to illustrate research findings)",
                        "Humorous": "Humorous (light-hearted and engaging presentation)",
                        "Optimistic": "Optimistic (highlighting positive findings and potential benefits)",
                        "Pessimistic": "Pessimistic (focusing on limitations and challenges)",
                    },
                }

                html: str = template.render(**context)

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
                return
            except Exception as e:
                logger.exception(f"Error rendering template: {e.__class__.__name__}: {e}")
                self.send_error(500, "Internal server error")
                return

        if self.path.startswith("/static/") or self.path.startswith("/outputs/"):
            try:
                file: str = self.path[1:]
                file_path: Path = SCRIPT_DIR / file

                if not file_path.exists():
                    self.send_error(404, "File not found")
                    return

                file_size = file_path.stat().st_size

                self.send_response(200)

                ext: str = os.path.splitext(file_path)[1]
                content_type: str | None = mimetypes.guess_type(file_path)[0]
                if not content_type and ext in mimetypes.types_map:
                    content_type = mimetypes.types_map[ext]
                if not content_type:
                    content_type = "application/octet-stream"

                if self.path.startswith("/outputs/"):
                    filename = os.path.basename(file_path)
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')

                self.send_header("Content-type", content_type)
                self.send_header("Content-Length", str(file_size))
                self.end_headers()

                data = file_path.read_bytes()
                chunk_size = 8192
                for i in range(0, len(data), chunk_size):
                    chunk = data[i : i + chunk_size]
                    self.wfile.write(chunk)
                    self.wfile.flush()

            except Exception as e:
                logger.exception(f"Error serving static file: {e.__class__.__name__}: {e}")
                self.send_error(500, "Internal server error")
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
                    async for chunk in self.stream_research(params):
                        self.wfile.write(chunk.encode())
                        self.wfile.flush()

                loop.run_until_complete(stream())
                loop.close()

            except Exception as e:
                logger.exception(f"Error conducting research: {e.__class__.__name__}: {e}")
                error_msg: str = json.dumps({"error": f"{e.__class__.__name__}: {e}"})
                self.wfile.write(f"data: {error_msg}\n\n".encode())
                self.wfile.flush()
                return
        else:
            self.send_error(404, "Not found")
            return

    def do_POST(self) -> None:
        """Handle POST requests - process file uploads and research requests"""
        if not self.path.startswith("/research"):
            self.send_error(404, "Not found")
            return

        try:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_error(400, "Expected multipart/form-data")
                return

            boundary: bytes = content_type.split("=")[1].encode()
            content_length = int(self.headers.get("Content-Length", 0))

            body: bytes = self.rfile.read(content_length)

            params: dict[str, Any] = {}
            document_paths: list[str] = []

            parts: list[bytes] = body.split(b"--" + boundary)

            for part in parts[1:-1]:
                try:
                    headers, content = part.split(b"\r\n\r\n", 1)
                    headers = headers.decode()

                    if "Content-Disposition" not in headers:
                        continue

                    name = None
                    filename = None
                    # Split only the Content-Disposition header
                    content_disp = next((line for line in headers.split("\r\n") if line.startswith("Content-Disposition")), "")

                    # Parse the Content-Disposition header
                    for item in content_disp.split(";"):
                        item = item.strip()
                        if item.startswith("name="):
                            name = item[5:].strip("\"'")
                        elif item.startswith("filename="):
                            filename = item[9:].strip("\"'")

                    if not name:
                        continue

                    if filename and filename.strip():
                        content: bytes = content[:-2] if content.endswith(b"\r\n") else content

                        file_path: Path = SCRIPT_DIR / "uploads" / filename
                        file_path.parent.mkdir(exist_ok=True, parents=True)
                        file_path.write_bytes(content)
                        document_paths.append(str(file_path))
                    else:
                        value: str = content.decode(errors="ignore").strip()
                        if value.endswith("\r\n"):
                            value = value[:-2]
                        params[name] = value
                except Exception as e:
                    logger.error(f"Error processing form part: {e}")
                    continue

            params["document_urls"] = document_paths

            self.send_response(200)
            self.send_header("Content-type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def stream() -> None:
                async for chunk in self.stream_research(params):
                    self.wfile.write(chunk.encode())
                    self.wfile.flush()

            loop.run_until_complete(stream())
            loop.close()

        except Exception as e:
            logger.exception(f"Error handling POST request: {e}")
            self.send_error(500, "Internal server error")
            return

    async def stream_research(
        self,
        params: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Stream the research process with progress updates"""
        try:
            manager = WebSocketManager()
            message_queue = asyncio.Queue()
            http_adapter = HTTPStreamAdapter(message_queue)
            await manager.connect(http_adapter)

            task: str = params["query"]
            report_type: str = params["report_type"]

            source_urls: list[str] | None = str(params.get("source_urls", "")).split(",") if params.get("source_urls") else None
            query_domains: list[str] = str(params.get("query_domains", "")).split(",") if params.get("query_domains") else []

            config_path: Path = SCRIPT_DIR / "config.json"
            config: Config = Config.from_path(config_path)

            config.CURATE_SOURCES = str(params.get("curate_sources", config.CURATE_SOURCES)).lower() == "true"
            config.EMBEDDING_KWARGS = json.loads(params.get("embedding_kwargs", json.dumps(config.EMBEDDING_KWARGS))) or config.EMBEDDING_KWARGS
            config.EMBEDDING_MODEL = params.get("embedding_model", config.EMBEDDING_MODEL) or config.EMBEDDING_MODEL
            config.EMBEDDING_PROVIDER = params.get("embedding_provider", config.EMBEDDING_PROVIDER) or config.EMBEDDING_PROVIDER
            config.EMBEDDING = params.get("embedding", config.EMBEDDING) or config.EMBEDDING
            config.FALLBACK_MODELS = str(params.get("fallback_models", "")).split(",") if params.get("fallback_models") else config.FALLBACK_MODELS
            config.FAST_LLM_MODEL = params.get("fast_llm_model", config.FAST_LLM_MODEL) or config.FAST_LLM_MODEL
            config.FAST_LLM_PROVIDER = params.get("fast_llm_provider", config.FAST_LLM_PROVIDER) or config.FAST_LLM_PROVIDER
            config.FAST_LLM = params.get("fast_llm", config.FAST_LLM) or config.FAST_LLM
            config.FAST_TOKEN_LIMIT = int(params.get("fast_token_limit", config.FAST_TOKEN_LIMIT)) or config.FAST_TOKEN_LIMIT
            config.LANGUAGE = params.get("language", config.LANGUAGE) or config.LANGUAGE
            config.MAX_ITERATIONS = int(params.get("max_iterations", config.MAX_ITERATIONS)) or config.MAX_ITERATIONS
            config.MAX_SEARCH_RESULTS_PER_QUERY = int(params.get("max_search_results_per_query", config.MAX_SEARCH_RESULTS_PER_QUERY)) or config.MAX_SEARCH_RESULTS_PER_QUERY
            config.MAX_SUBTOPICS = int(params.get("max_subtopics", config.MAX_SUBTOPICS)) or config.MAX_SUBTOPICS
            config.MEMORY_BACKEND = ReportSource(str(params.get("memory_backend", config.MEMORY_BACKEND.value)) or config.MEMORY_BACKEND.value)
            config.REPORT_FORMAT = ReportFormat.__members__[str(params.get("report_format", config.REPORT_FORMAT.name)).upper() or config.REPORT_FORMAT.name]
            config.REPORT_SOURCE = ReportSource(str(params.get("report_source", config.REPORT_SOURCE.value)) or config.REPORT_SOURCE.value)
            config.REPORT_TYPE = ReportType.__members__[str(params.get("report_type", config.REPORT_TYPE.name)) or config.REPORT_TYPE.name]
            config.RESEARCH_PLANNER = params.get("research_planner", config.RESEARCH_PLANNER) or config.RESEARCH_PLANNER
            config.RETRIEVER = params.get("retriever", config.RETRIEVER) or config.RETRIEVER
            config.SCRAPER = params.get("scraper", config.SCRAPER) or config.SCRAPER
            config.SIMILARITY_THRESHOLD = float(params.get("similarity_threshold", config.SIMILARITY_THRESHOLD)) or config.SIMILARITY_THRESHOLD
            config.SMART_LLM_MODEL = params.get("smart_llm_model", config.SMART_LLM_MODEL) or config.SMART_LLM_MODEL
            config.SMART_LLM_PROVIDER = params.get("smart_llm_provider", config.SMART_LLM_PROVIDER) or config.SMART_LLM_PROVIDER
            config.SMART_LLM = params.get("smart_llm", config.SMART_LLM) or config.SMART_LLM
            config.SMART_TOKEN_LIMIT = int(params.get("smart_token_limit", config.SMART_TOKEN_LIMIT)) or config.SMART_TOKEN_LIMIT
            config.STRATEGIC_LLM_MODEL = params.get("strategic_llm_model", config.STRATEGIC_LLM_MODEL) or config.STRATEGIC_LLM_MODEL
            config.STRATEGIC_LLM_PROVIDER = params.get("strategic_llm_provider", config.STRATEGIC_LLM_PROVIDER) or config.STRATEGIC_LLM_PROVIDER
            config.STRATEGIC_LLM = params.get("strategic_llm", config.STRATEGIC_LLM) or config.STRATEGIC_LLM
            config.STRATEGIC_TOKEN_LIMIT = params.get("strategic_token_limit", config.STRATEGIC_TOKEN_LIMIT) or config.STRATEGIC_TOKEN_LIMIT
            config.TEMPERATURE = float(params.get("temperature", config.TEMPERATURE)) or config.TEMPERATURE
            config.TONE = Tone.__members__[str(params.get("tone", config.TONE.name) or config.TONE.name).capitalize()] or config.TONE
            config.TOTAL_WORDS = int(params.get("total_words", config.TOTAL_WORDS) or config.TOTAL_WORDS)
            config.USE_FALLBACKS = str(params.get("use_fallbacks", config.USE_FALLBACKS) or config.USE_FALLBACKS).lower() == "true"
            config.USER_AGENT = params.get("user_agent", config.USER_AGENT) or config.USER_AGENT
            config.VERBOSE = str(params.get("verbose", config.VERBOSE)).lower() == "true" or config.VERBOSE

            config_path.write_text(config.to_json())

            yield "Starting research process...\n"
            yield f"Query: {task}\n"
            yield f"Report Type: {report_type}\n"

            if query_domains:
                yield f"Searching in domains: {', '.join(query_domains)}\n"

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

            await manager.disconnect(http_adapter)

        except Exception as e:
            logger.exception(f"Error in research stream: {e.__class__.__name__}: {e}")
            yield f"\nError: {e.__class__.__name__}: {e}\n"
            raise


def run_server(port: int = 8080) -> None:
    """Run the web server on the specified port"""
    load_dotenv()

    class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    with ThreadingHTTPServer(("", port), AsyncStreamingResearchRequestHandler) as httpd:
        logger.info(f"Server started at http://localhost:{port}")
        logger.info("Using threaded server that can handle multiple concurrent connections")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the GPT Researcher web server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on (default: 8080)")
    args: argparse.Namespace = parser.parse_args()
    run_server(port=args.port)
