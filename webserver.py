from __future__ import annotations

import argparse
import asyncio
import http.server
import json
import logging
import mimetypes
import os
import socketserver
import urllib.parse

from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import uuid4

from dotenv import load_dotenv
from gpt_researcher import GPTResearcher
from gpt_researcher.config import Config
from gpt_researcher.utils.enum import (
    OutputFileType,
    ReportFormat,
    ReportSource,
    ReportType,
    SupportedLanguages,
    Tone,
)
from langchain.schema import Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/webserver.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Initialize MIME types
mimetypes.init()
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('text/html', '.html')

# Create logs and outputs directories if they don't exist
for dir_path in ["logs", "outputs"]:
    Path(dir_path).mkdir(exist_ok=True, parents=True)


class AsyncStreamingResearchRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        """Handle GET requests - serve static files and the HTML form"""
        if self.path == "/":
            self.path = "/static/templates/index.html"
        
        # Handle static file requests
        if self.path.startswith("/static/"):
            try:
                file: str = self.path[1:]  # Remove leading slash
                file_path: Path = Path(file)
                self.send_response(200)
                print(f"Serving file: {file_path}")
                # Set content type based on file extension
                ext: str = os.path.splitext(file_path)[1]
                content_type: str | None = mimetypes.guess_type(file_path)[0]
                if not content_type and ext in mimetypes.types_map:
                    content_type = mimetypes.types_map[ext]
                if not content_type:
                    content_type = 'application/octet-stream'
                self.send_header("Content-type", content_type)
                self.end_headers()
                print(f"Content type: {content_type}")
                
                # Read file in binary mode
                file_contents: bytes = file_path.read_bytes()
                self.wfile.write(file_contents)
            except Exception as e:
                logger.exception(f"Error serving static file: {e.__class__.__name__}: {e}")
                self.send_error(500, "Internal server error")
            return

        if self.path.startswith("/research"):
            parsed_url: urllib.parse.ParseResult = urllib.parse.urlparse(self.path)
            params: dict[str, Any] = dict(urllib.parse.parse_qsl(parsed_url.query))

            # Validate required parameters
            if not params.get("query") or not params.get("report_type"):
                self.send_error(400, "Missing required parameters: query and report_type")
                return

            try:
                self.send_response(200)
                self.send_header("Content-type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()

                # Create event loop for async operations
                loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Run the research stream
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

    async def stream_research(
        self,
        params: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Stream the research process with progress updates"""
        try:
            # Basic parameters
            query: str = params["query"]
            report_type: ReportType = ReportType(params["report_type"])
            report_format: ReportFormat = ReportFormat(params.get("report_format", ReportFormat.APA.value))
            output_format: OutputFileType = OutputFileType(params.get("output_format", OutputFileType.MARKDOWN.value))
            report_source: ReportSource = ReportSource(params.get("report_source", ReportSource.Web.value))
            tone: Tone = Tone.__members__[str(params.get("tone", Tone.Objective.value)).capitalize()]
            language: SupportedLanguages = SupportedLanguages(params.get("language", "en"))

            # Source URLs and domains
            source_urls: list[str] | None = str(params.get("source_urls", "")).split(",") if params.get("source_urls") else None
            query_domains: list[str] = str(params.get("query_domains", "")).split(",") if params.get("query_domains") else []

            # Advanced parameters
            agent_role: str | None = params.get("agent_role")
            max_subtopics: int = int(params.get("max_subtopics", 10))
            verbose: bool = params.get("verbose", "true").lower() == "true"
            complement_source_urls: bool = params.get("complement_source_urls", "false").lower() == "true"

            # Handle document uploads if present
            documents: list[dict[str, Any] | Document] | None = None
            if "documents" in params:
                documents = []
                for file_data in params["documents"]:
                    # Process uploaded files
                    pass

            # Configure research settings
            config = Config()
            config.LANGUAGE = SupportedLanguages(language)
            config.MAX_SUBTOPICS = max_subtopics
            config.VERBOSE = verbose

            yield "Starting research process...\n"
            yield f"Query: {query}\n"
            yield f"Report Type: {report_type}\n"
            yield f"Format: {report_format}\n"

            if source_urls:
                yield f"Using specified sources: {', '.join(source_urls)}\n"
            if query_domains:
                yield f"Searching in domains: {', '.join(query_domains)}\n"

            researcher = GPTResearcher(
                query=query,
                report_type=report_type,
                report_format=report_format,
                output_file_type=output_format,
                report_source=report_source,
                tone=tone,
                source_urls=source_urls,
                documents=documents,
                complement_source_urls=complement_source_urls,
                config=config,
                agent_role=agent_role,
                verbose=verbose,
                query_domains=query_domains,
            )

            yield "Gathering information from various sources...\n"
            _research_result: list[str] = await researcher.conduct_research()

            yield "Analyzing and synthesizing findings...\n"
            report: str = await researcher.write_report()

            # Save report to file with appropriate extension
            extension: str = ".md" if output_format == OutputFileType.MARKDOWN else f".{output_format.value.lower()}"
            output_path: Path = Path("outputs", f"{uuid4().hex[:8]}{extension}")
            output_path.write_text(report)
            logger.info(f"Report saved to {output_path}")

            yield "\n--- Research Report ---\n\n"
            yield report
            yield f"\n\nReport saved to: {output_path}\n"

        except Exception as e:
            logger.exception(f"Error in research stream: {e.__class__.__name__}: {e}")
            yield f"\nError: {e.__class__.__name__}: {e}\n"
            raise


def run_server(port: int = 8080) -> None:
    """Run the web server on the specified port"""
    load_dotenv()  # Load environment variables

    with socketserver.TCPServer(("", port), AsyncStreamingResearchRequestHandler) as httpd:
        logger.info(f"Server started at http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the GPT Researcher web server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on (default: 8080)')
    args = parser.parse_args()
    run_server(port=args.port)

# python webserver.py --port 8080
