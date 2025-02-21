from __future__ import annotations

import asyncio
import logging

from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from gpt_researcher.actions import stream_output
from gpt_researcher.utils.enum import ReportType, Tone
from multi_agents.main import run_research_task

from backend.chat import ChatAgentWithMemory
from backend.report_type import BasicReporter, DetailedReporter
from backend.server.server_utils import CustomLogsHandler

logger: logging.Logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage websockets"""

    def __init__(self):
        """Initialize the WebSocketManager class."""
        self.active_connections: list[WebSocket] = []
        self.sender_tasks: dict[WebSocket, asyncio.Task] = {}
        self.message_queues: dict[WebSocket, asyncio.Queue] = {}
        self.chat_agent: ChatAgentWithMemory | None = None

    async def start_sender(
        self,
        websocket: WebSocket,
    ):
        """Start the sender task."""
        queue: asyncio.Queue | None = self.message_queues.get(websocket)
        if not queue:
            return

        while True:
            message: Any = await queue.get()
            if websocket in self.active_connections:
                try:
                    if message == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
                except Exception as e:
                    logger.exception(f"Error sending message: {e.__class__.__name__}: {e}")
                    break
            else:
                break

    async def connect(
        self,
        websocket: WebSocket,
    ):
        """Connect a websocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queues[websocket] = asyncio.Queue()
        self.sender_tasks[websocket] = asyncio.create_task(self.start_sender(websocket))

    async def disconnect(
        self,
        websocket: WebSocket,
    ):
        """Disconnect a websocket."""
        if websocket not in self.active_connections:
            return
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
        tone: Tone | str,
        websocket: WebSocket,
        headers: dict[str, str] | None = None,
        query_domains: list[str] | None = None,
    ):
        """Start streaming the output."""
        query_domains = [] if query_domains is None else query_domains
        tone = Tone.__members__[tone.lower().capitalize()] if isinstance(tone, str) else tone
        # add customized JSON config file path here
        config_path = "default"
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
        # Create new Chat Agent whenever a new report is written
        self.chat_agent = ChatAgentWithMemory(report, config_path, headers)
        return report

    async def chat(
        self,
        message: str,
        websocket: WebSocket,
    ) -> str | None:
        """Chat with the agent based message diff"""
        if self.chat_agent is not None:
            return await self.chat_agent.chat(message, websocket)
        await websocket.send_json(
            {
                "type": "chat",
                "content": "Knowledge empty, please run the research first to obtain knowledge",
            }
        )
        return None


async def run_agent(
    task: str,
    report_type: str | ReportType,
    report_source: str,
    source_urls: list[str],
    document_urls: list[str],
    tone: Tone,
    websocket: WebSocket,
    headers: dict[str, str] | None = None,
    query_domains: list[str] = [],
    config_path: str = "",
) -> str:
    """Run the agent."""
    report_type = ReportType(report_type.title()) if isinstance(report_type, str) else report_type
    # Create logs handler for this research task
    logs_handler = CustomLogsHandler(websocket, task)

    start_time: datetime = datetime.now(timezone.utc)
    # Instead of running the agent directly run it through the different report type classes
    if report_type == ReportType.MultiAgents:
        report = await run_research_task(
            query=task,
            websocket=logs_handler,  # Use logs_handler instead of raw websocket
            stream_output=stream_output,
            tone=tone,
            headers=headers,
        )
        report = report.get("report", "") if isinstance(report, dict) else report

    elif report_type == ReportType.DetailedReport:
        researcher = DetailedReporter(
            query=task,
            query_domains=query_domains,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=(
                logs_handler.websocket
                if isinstance(logs_handler, CustomLogsHandler)
                else logs_handler
            ),  # Use logs_handler instead of raw websocket
            headers=headers,
        )
        report = await researcher.run()
    else:
        researcher = BasicReporter(
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

    # measure time
    end_time: datetime = datetime.now(timezone.utc)
    await websocket.send_json(
        {
            "type": "logs",
            "output": f"\nTotal run time: {end_time - start_time}\n",
        }
    )

    return report
