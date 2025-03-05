from __future__ import annotations

import asyncio
import json
import re

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket
from gpt_researcher.actions import stream_output  # Import stream_output
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone
from gpt_researcher.utils.logger import get_formatted_logger
from multi_agents.main import run_research_task

from backend.chat import ChatAgentWithMemory
from backend.report_type import BasicReport, DetailedReport
from backend.report_type.deep_research.example import DeepResearch
from backend.server.server_utils import CustomLogsHandler

if TYPE_CHECKING:
    import logging

    from backend.server.server_utils import HTTPStreamAdapter

logger: logging.Logger = get_formatted_logger(__name__)


class WebSocketManager:
    """Manage websockets."""

    def __init__(self):
        """Initialize the WebSocketManager class."""
        self.active_connections: list[WebSocket | HTTPStreamAdapter] = []
        self.sender_tasks: dict[WebSocket | HTTPStreamAdapter, asyncio.Task] = {}
        self.message_queues: dict[WebSocket | HTTPStreamAdapter, asyncio.Queue[str]] = {}
        self.chat_agent: ChatAgentWithMemory | None = None

    async def start_sender(
        self,
        websocket: WebSocket | HTTPStreamAdapter,
    ):
        """Start the sender task."""
        queue: asyncio.Queue[str] | None = self.message_queues.get(websocket)
        if queue is None:
            return

        while True:
            message: str = await queue.get()
            if websocket in self.active_connections:
                try:
                    if message == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
                except Exception as e:
                    logger.exception(f"Error sending message! {e.__class__.__name__}: {e}")
                    break
            else:
                break

    async def connect(
        self,
        websocket: WebSocket | HTTPStreamAdapter,
    ):
        """Connect a websocket."""
        if isinstance(websocket, WebSocket):
            await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queues[websocket] = asyncio.Queue()
        self.sender_tasks[websocket] = asyncio.create_task(self.start_sender(websocket))

    async def disconnect(
        self,
        websocket: WebSocket | HTTPStreamAdapter,
    ):
        """Disconnect a websocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.sender_tasks:
                self.sender_tasks[websocket].cancel()
                await self.message_queues[websocket].put("close")
                del self.sender_tasks[websocket]
                del self.message_queues[websocket]

    async def start_streaming(
        self,
        task: str,
        report_type: str,
        report_source: str,
        source_urls: list[str],
        document_urls: list[str],
        tone: Tone | str,
        websocket: WebSocket | HTTPStreamAdapter,
        headers: dict[str, str] | None = None,
        query_domains: list[str] | None = None,
    ) -> str:
        """Start streaming the output."""
        logger.info(f"Starting research: {task}")

        # add customized JSON config file path here
        config_path = "default"

        # Generate a sanitized filename for the report
        base_filename = self._generate_filename(task)

        try:
            # Run the research agent
            report: str = await run_agent(
                task,
                report_type,
                report_source,
                source_urls,
                document_urls,
                tone,
                websocket,
                headers=headers,
                query_domains=query_domains,
                config_path=config_path,
            )

            logger.info(f"Research completed for: {task}")

            # Create new Chat Agent whenever a new report is written
            self.chat_agent = ChatAgentWithMemory(report, config_path, headers)

            # Save the report to files
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)

            # Save markdown version
            md_path = output_dir / f"{base_filename}.md"
            md_path.write_text(report)
            logger.info(f"Report saved to {md_path}")

            # Send report completion notification to the frontend
            await self._send_report_complete_notification(websocket, report, base_filename)

            return report

        except Exception as e:
            logger.exception(f"Error in research process: {e}")
            # Notify the frontend about the error
            await websocket.send_json({"type": "error", "message": f"Research failed: {str(e)}"})
            return ""

    def _generate_filename(self, task: str) -> str:
        """Generate a sanitized filename for the report."""
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Sanitize the task for use in a filename
        sanitized_task: str = re.sub(r"[^\w\s-]", "", task)
        sanitized_task = re.sub(r"\s+", "_", sanitized_task)

        # Truncate if too long
        if len(sanitized_task) > 50:
            sanitized_task = sanitized_task[:50]

        return f"report_{timestamp}_{sanitized_task}"

    async def _send_report_complete_notification(
        self, websocket: WebSocket | HTTPStreamAdapter, report: str, base_filename: str
    ) -> None:
        """Send report completion notification to the frontend."""
        logger.info("Sending report completion notification to frontend")

        # Create file URLs for download
        files: dict[str, str] = {
            "md": f"/download/{base_filename}.md",
            "pdf": f"/download/{base_filename}.pdf",
            "docx": f"/download/{base_filename}.docx",
        }

        # Format the notification as a server-sent event
        notification: dict[str, Any] = {
            "type": "report_complete",
            "content": report,
            "base_filename": base_filename,
            "files": files,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        }

        # Send as JSON
        await websocket.send_json(notification)

        # Also send individual file_ready notifications for each format
        for fmt in ["md", "pdf", "docx"]:
            await websocket.send_json(
                {
                    "type": "file_ready",
                    "format": fmt,
                    "url": files[fmt],
                }
            )

        # Send files_ready notification
        await websocket.send_json(
            {
                "type": "files_ready",
                "message": "All output files have been generated.",
                "files": files,
            }
        )

        # Also send as a data event for SSE clients
        sse_message = f"data: {json.dumps(notification)}\n\n"
        await websocket.send_text(sse_message)

        logger.info("Report completion notification sent")

    async def chat(
        self,
        message: str,
        websocket: WebSocket | HTTPStreamAdapter,
    ) -> str | None:
        """Chat with the agent based message diff."""
        if self.chat_agent:
            return await self.chat_agent.chat(message, websocket)
        await websocket.send_json(
            {
                "type": "chat",
                "content": "Knowledge empty, please run the research first to obtain knowledge",
            }
        )


async def run_agent(
    task: str,
    report_type: str | ReportType,
    report_source: str | ReportSource,
    source_urls: list[str] | None = None,
    document_urls: list[str] | None = None,
    tone: Tone | str | None = None,
    websocket: WebSocket | HTTPStreamAdapter | None = None,
    headers: dict[str, str] | None = None,
    query_domains: list[str] | None = None,
    config_path: str = "",
) -> str:
    """Run the agent."""
    # Create logs handler for this research task
    logs_handler = CustomLogsHandler(websocket, task)
    tone = (
        Tone.__members__[tone.capitalize()]
        if isinstance(tone, str) and tone.capitalize() in Tone.__members__
        else tone
        if isinstance(tone, Tone)
        else Tone(tone)
        if tone is not None
        else Tone.Objective
    )
    report_type = (
        ReportType.__members__[report_type]
        if isinstance(report_type, str) and report_type in ReportType.__members__
        else report_type
        if isinstance(report_type, ReportType)
        else ReportType(report_type)
    )
    report_source = (
        ReportSource.__members__[report_source]
        if isinstance(report_source, str) and report_source in ReportSource.__members__
        else report_source
        if isinstance(report_source, ReportSource)
        else ReportSource(report_source)
    )
    # Initialize researcher based on report type
    if report_type == ReportType.MultiAgents:
        report: str = await run_research_task(
            query=task,
            websocket=logs_handler,
            stream_output=stream_output,
            tone=tone,
            headers=headers,
        )

    elif report_type == ReportType.DetailedReport:
        researcher = DetailedReport(
            query=task,
            query_domains=query_domains,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,
            headers=headers,
        )
        report = await researcher.run()

    elif report_type == ReportType.ResearchReport:
        researcher = BasicReport(
            query=task,
            query_domains=query_domains,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,
            headers=headers,
        )
        report = await researcher.run()

    elif report_type == ReportType.DeepResearch:
        researcher = DeepResearch(
            query=task,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,
            headers=headers,
            concurrency_limit=2,
        )
        report = await researcher.run()

    else:
        raise ValueError(
            f"Invalid report type: {report_type!r}: must be MultiAgents, DetailedReport, DeepResearch, or ResearchReport"
        )

    return report
