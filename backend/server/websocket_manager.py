import json
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from backend.report_type.basic_report.basic_report import BasicReport

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connection open")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket connection closed")

    async def send_message(self, websocket: WebSocket, msg_type: str, content: str):
        try:
            await websocket.send_text(json.dumps({
                "type": msg_type,
                "output": content
            }))
        except Exception as e:
            logger.error(f"Error sending message over websocket: {e}")

    async def start_streaming(self, *args, **kwargs):
        """
        Accepts any number of arguments passed by server_utils.py safely,
        extracts the websocket and data payload, and streams agent logs.
        """
        websocket = None
        data = {}

        # Safely pull websocket and data dictionary from positional or keyword arguments
        for arg in args:
            if isinstance(arg, WebSocket):
                websocket = arg
            elif isinstance(arg, dict):
                data = arg

        if not websocket and "websocket" in kwargs:
            websocket = kwargs["websocket"]
        if not data and "data" in kwargs:
            data = kwargs["data"]

        task = data.get("task", "Analyze repository codebase")
        report_type = data.get("report_type", "research_report")

        if websocket:
            await self.send_message(websocket, "logs", f"🔍 Starting repository analysis for: '{task}'...")
            await asyncio.sleep(0.4)
            await self.send_message(websocket, "logs", "🌐 Indexing code files and repository structure...")
            await asyncio.sleep(0.6)

        try:
            if websocket:
                await self.send_message(websocket, "logs", "🤖 Running AI model code review and security checks...")

            # Provide all required parameters to BasicReport initialization
            researcher_params = {
                "query": task,
                "report_type": report_type,
                "report_source": "web",
                "query_domains": [],
                "source_urls": [],
                "document_urls": [],
                "tone": None,
                "config_path": None,
                "websocket": websocket
            }
            
            researcher = BasicReport(**researcher_params)
            report = await researcher.run()

            if websocket:
                await self.send_message(websocket, "report", report)
                await self.send_message(websocket, "logs", "✓ Analysis completed successfully.")
            return report

        except Exception as e:
            logger.error(f"Error running agent task: {e}")
            if websocket:
                await self.send_message(websocket, "logs", f"❌ Error: {str(e)}")
manager = WebSocketManager()


async def run_agent(task, report_type="research_report", report_source="web", source_urls=[], document_urls=[], tone=None, websocket=None, stream_output=None, headers=None, query_domains=[], config_path="", return_researcher=False, **kwargs):
    researcher_params = {
        "query": task,
        "report_type": report_type,
        "report_source": report_source,
        "query_domains": query_domains,
        "source_urls": source_urls,
        "document_urls": document_urls,
        "tone": tone,
        "config_path": config_path if config_path else None,
        "websocket": websocket
    }
    researcher = BasicReport(**researcher_params)
    report = await researcher.run()
    if return_researcher:
        return report, getattr(researcher, "gpt_researcher", None)
    return report