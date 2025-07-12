from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from fastapi import WebSocket

from backend.chat.chat import ChatAgentWithMemory
from backend.report_type.basic_report.basic_report import BasicReport
from backend.report_type.detailed_report.detailed_report import DetailedReport
from backend.server.server_utils import CustomLogsHandler
from gpt_researcher.actions import stream_output
from gpt_researcher.utils.enum import ReportType, Tone
from multi_agents.main import run_research_task

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher


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
        queue: asyncio.Queue[str | None] | None = self.message_queues.get(websocket)
        if not queue:
            return

        while True:
            try:
                message: str | None = await queue.get()
                if message is None:  # Shutdown signal
                    break

                if websocket in self.active_connections:
                    if message == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
                else:
                    break
            except Exception as e:
                print(f"Error in sender task: {e.__class__.__name__}: {e}")
                break

    async def connect(self, websocket: WebSocket):
        """Connect a websocket."""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.message_queues[websocket] = asyncio.Queue()
            self.sender_tasks[websocket] = asyncio.create_task(
                self.start_sender(websocket)
            )
        except Exception as e:
            print(f"Error connecting websocket: {e.__class__.__name__}: {e}")
            if websocket in self.active_connections:
                await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        if websocket in self.active_connections:
            if websocket in self.sender_tasks:
                self.sender_tasks[websocket].cancel()
                await self.message_queues[websocket].put(None)
                del self.sender_tasks[websocket]
            if websocket in self.message_queues:
                del self.message_queues[websocket]
            try:
                await websocket.close()
            except Exception as e:
                print(
                    f"Error closing websocket: Connection might already be closed (ignore this error): {e.__class__.__name__}: {e}"
                )
            self.active_connections.remove(websocket)

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
        mcp_enabled: bool = False,
        mcp_strategy: str = "fast",
        mcp_configs: list[str] = [],
        **kwargs,
    ) -> str:
        """Start streaming the output."""
        tone = Tone[tone] if isinstance(tone, str) else tone
        # add customized JSON config file path here
        config_path: str = "default"
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
            query_domains=query_domains,
            mcp_enabled=mcp_enabled,
            mcp_strategy=mcp_strategy,
            mcp_configs=mcp_configs,
            **kwargs,
        )
        # Create new Chat Agent whenever a new report is written
        self.chat_agent = ChatAgentWithMemory(report, config_path, headers)
        return report

    async def chat(
        self,
        message: str,
        websocket: WebSocket,
    ):
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
    query_domains: list[str] | None = None,
    return_researcher: bool = False,
    stream_output: Callable[[str, WebSocket], Awaitable[None]] | None = stream_output,
    mcp_enabled: bool = False,
    mcp_strategy: str = "fast",
    mcp_configs: list[str] | None = None,
    **kwargs,
) -> str | tuple[str, GPTResearcher]:
    """Run the agent."""
    start_time: datetime.datetime = datetime.datetime.now()

    # Create logs handler for this research task
    logs_handler: CustomLogsHandler = CustomLogsHandler(websocket, task)

    # Set up MCP configuration if enabled
    if mcp_enabled and mcp_configs:
        import os

        current_retriever = os.getenv("RETRIEVER", "tavily")
        if "mcp" not in current_retriever:
            # Add MCP to existing retrievers
            os.environ["RETRIEVER"] = f"{current_retriever},mcp"

        # Set MCP strategy
        os.environ["MCP_STRATEGY"] = mcp_strategy

        print(
            f"🔧 MCP enabled with strategy '{mcp_strategy}' and {len(mcp_configs)} server(s)"
        )
        await logs_handler.send_json(
            {
                "type": "logs",
                "content": "mcp_init",
                "output": f"🔧 MCP enabled with strategy '{mcp_strategy}' and {len(mcp_configs)} server(s)",
            }
        )

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
            query_domains=query_domains,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,  # Use logs_handler instead of raw websocket
            headers=headers,
            mcp_configs=None if not mcp_enabled else mcp_configs,
            mcp_strategy=None if not mcp_enabled else mcp_strategy,
        )
        report_content = await researcher.run()

    elif report_type == ReportType.DeepResearch.value:
        # For deep research, we use the BasicReport to pass through to the GPTResearcher
        # which handles deep research through its internal mechanism
        researcher = BasicReport(
            query=task,
            query_domains=query_domains,
            report_type=report_type,  # Pass the DeepResearch value correctly
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,
            headers=headers,
            mcp_configs=mcp_configs if mcp_enabled else None,
            mcp_strategy=mcp_strategy if mcp_enabled else None,
        )
        report_content = await researcher.run()

    else:
        # For other standard report types (research_report, resource_report, etc.)
        researcher = BasicReport(
            query=task,
            query_domains=query_domains,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,
            config_path=config_path,
            websocket=logs_handler,  # Use logs_handler instead of raw websocket
            headers=headers,
            mcp_configs=mcp_configs if mcp_enabled else None,
            mcp_strategy=mcp_strategy if mcp_enabled else None,
        )
        report_content: str = await researcher.run()

    end_time: datetime.datetime = datetime.datetime.now()
    duration: datetime.timedelta = end_time - start_time
    print(f"Research for task: {task} completed in {duration}")

    if report_type != "multi_agents" and return_researcher:
        return report_content, researcher.gpt_researcher
    else:
        return report_content
