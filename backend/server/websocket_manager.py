from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket

from backend.chat import ChatAgentWithMemory
from backend.report_type import BasicReport, DetailedReport
from backend.server.server_utils import CustomLogsHandler
from gpt_researcher.actions import stream_output  # Import stream_output
from gpt_researcher.utils.enum import ReportType, Tone
from multi_agents.main import run_research_task

if TYPE_CHECKING:
    from fastapi import WebSocket


class WebSocketManager:
    """Manage websockets"""

    def __init__(self):
        """Initialize the WebSocketManager class."""
        self.active_connections: list[WebSocket] = []
        self.sender_tasks: dict[WebSocket, asyncio.Task] = {}
        self.message_queues: dict[WebSocket, asyncio.Queue] = {}
        self.chat_agent: ChatAgentWithMemory | None = None

    async def start_sender(self, websocket: WebSocket):
        """Start the sender task."""
        queue: asyncio.Queue | None = self.message_queues.get(websocket)
        if not queue:
            return

        while True:
            message: str | None = await queue.get()
            if websocket in self.active_connections:
                try:
                    if message == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
                except Exception:
                    break
            else:
                break

    async def connect(self, websocket: WebSocket):
        """Connect a websocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queues[websocket] = asyncio.Queue()
        self.sender_tasks[websocket] = asyncio.create_task(self.start_sender(websocket))

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.sender_tasks[websocket].cancel()
            await self.message_queues[websocket].put(None)
            del self.sender_tasks[websocket]
            del self.message_queues[websocket]

    async def start_streaming(
        self,
        task: str,
        report_type: str,
        report_source: str,
        source_urls: list[str],
        document_urls: list[str],
        tone: Tone,
        websocket: WebSocket,
        headers: dict[str, str] | None = None,
        **kwargs: dict[str, Any],
    ) -> str:
        """Start streaming the output."""
        tone = Tone[tone]
        # add customized JSON config file path here
        config_path = ""
        report: str = await run_agent(
            task,
            report_type,
            report_source,
            source_urls,
            document_urls,
            tone,
            websocket,
            headers=headers,
            config_path=config_path,
            **kwargs,
        )
        # Create new Chat Agent whenever a new report is written
        self.chat_agent = ChatAgentWithMemory(report, config_path, headers)
        return report

    async def chat(self, message: str, websocket: WebSocket):
        """Chat with the agent based message diff"""
        if self.chat_agent:
            await self.chat_agent.chat(message, websocket)
        else:
            await websocket.send_json(
                {
                    "type": "chat",
                    "content": "Knowledge empty, please run the research first to obtain knowledge",
                }
            )


async def run_agent(
    task: str,
    report_type: str,
    report_source: str,
    source_urls: list[str],
    document_urls: list[str],
    tone: Tone,
    websocket: WebSocket,
    headers: dict[str, str] | None = None,
    config_path: str = "",
    **kwargs: dict[str, Any],
) -> str:
    """Run the agent."""
    start_time: datetime.datetime = datetime.datetime.now()

    # Create logs handler for this research task
    logs_handler = CustomLogsHandler(websocket, task)

    # Validate report_type against known values
    valid_report_types: list[str] = [r.value for r in ReportType]

    if report_type not in valid_report_types and report_type != "multi_agents":
        error_message: str = f"Invalid report_type: '{report_type}'. Valid options are: {', '.join(valid_report_types + ['multi_agents'])}"
        await websocket.send_json({
            "type": "logs",
            "output": f'<div class="error-message">⚠️ {error_message}</div>'
        })
        raise ValueError(error_message)

    # Initialize researcher based on report type
    if report_type == "multi_agents":
        report: dict[str, Any] = await run_research_task(
            query=task,
            websocket=logs_handler,  # Use logs_handler instead of raw websocket
            stream_output=stream_output,
            tone=tone,
            headers=headers,
        )
        report_content: str = report.get("report", "")

    elif report_type == ReportType.DetailedReport.value:
        researcher = DetailedReport(
            query=task,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,  # Use logs_handler instead of raw websocket
            headers=headers,
        )
        report_content = await researcher.run()

    elif report_type == ReportType.DeepResearch.value:
        # For deep research, we use the BasicReport to pass through to the GPTResearcher
        # which handles deep research through its internal mechanism
        researcher = BasicReport(
            query=task,
            report_type=report_type,  # Pass the DeepResearch value correctly
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,
            headers=headers,
        )
        report_content = await researcher.run()

    else:
        # For other standard report types (research_report, resource_report, etc.)
        researcher = BasicReport(
            query=task,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,  # Use logs_handler instead of raw websocket
            headers=headers,
        )
        report_content = await researcher.run()

    end_time: datetime.datetime = datetime.datetime.now()
    duration: datetime.timedelta = end_time - start_time
    print(f"Research completed in {duration}")

    return report_content
