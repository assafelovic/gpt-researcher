"""
Task runner — the actual research execution, decoupled from WebSocket.

Called by TaskManager._run_task(). The `broadcast` callback fans log messages
out to all active subscribers (WebSocket connections watching this task).
"""

import asyncio
import logging
import os
import time
from typing import Callable, Awaitable

from server.server_utils import (
    sanitize_filename,
    generate_report_files,
    CustomLogsHandler,
    extract_command_data,
)
from server.websocket_manager import run_agent
from gpt_researcher.utils.enum import Tone

logger = logging.getLogger(__name__)


class QueuedLogsHandler:
    """
    Drop-in replacement for CustomLogsHandler that:
     1. Writes the JSON log file (same as before).
     2. Calls `broadcast(task, message)` so TaskManager can fan out to subscribers.

    The `websocket` attribute is set to None — the runner is WS-agnostic.
    """

    def __init__(self, task_obj, broadcast_fn):
        self._task = task_obj
        self._broadcast = broadcast_fn
        self.websocket = None  # run_agent checks this

        task = task_obj.params.get("task", "task")
        sanitized = sanitize_filename(f"task_{int(time.time())}_{task}")
        os.makedirs("outputs", exist_ok=True)
        import json
        from datetime import datetime
        self.log_file = os.path.join("outputs", f"{sanitized}.json")
        self.timestamp = datetime.now().isoformat()
        with open(self.log_file, "w") as f:
            json.dump(
                {
                    "task_id": task_obj.task_id,
                    "timestamp": self.timestamp,
                    "events": [],
                    "content": {
                        "query": task,
                        "sources": [],
                        "context": [],
                        "report": "",
                        "costs": 0.0,
                    },
                },
                f,
                indent=2,
            )

    async def send_json(self, data: dict) -> None:
        """Store + broadcast; never sends to WebSocket directly."""
        import json
        from datetime import datetime

        # Write to log file (same as CustomLogsHandler)
        with open(self.log_file, "r") as f:
            log_data = json.load(f)
        if data.get("type") == "logs":
            log_data["events"].append(
                {"timestamp": datetime.now().isoformat(), "type": "event", "data": data}
            )
        else:
            log_data["content"].update(data)
        with open(self.log_file, "w") as f:
            json.dump(log_data, f, indent=2)

        # Fan out to subscribers via TaskManager
        await self._broadcast(self._task, data)


async def run_research_task(task_obj, broadcast_fn: Callable) -> dict:
    """
    Execute a research task using the same run_agent() as the WebSocket path,
    but with a QueuedLogsHandler instead of a raw WebSocket.

    Returns file_paths dict: {pdf, docx, md, json}
    """
    params = task_obj.params
    logs_handler = QueuedLogsHandler(task_obj, broadcast_fn)

    # Extract params (same keys the WS path uses)
    task = params.get("task", "")
    report_type = params.get("report_type", "research_report")
    report_source = params.get("report_source", "web")
    source_urls = params.get("source_urls") or []
    document_urls = params.get("document_urls") or []
    tone_str = params.get("tone", "Objective")
    headers = params.get("headers") or {}
    query_domains = params.get("query_domains") or []
    mcp_enabled = params.get("mcp_enabled", False)
    mcp_strategy = params.get("mcp_strategy", "fast")
    mcp_configs = params.get("mcp_configs") or []
    max_search_results = params.get("max_search_results")
    config_path = os.environ.get("CONFIG_PATH", "default")

    tone = Tone[tone_str] if tone_str in Tone.__members__ else Tone.Objective

    # Notify subscribers that we started
    await broadcast_fn(task_obj, {
        "type": "task_status",
        "status": "running",
        "task_id": task_obj.task_id,
    })

    report = await run_agent(
        task=task,
        report_type=report_type,
        report_source=report_source,
        source_urls=source_urls,
        document_urls=document_urls,
        tone=tone,
        websocket=logs_handler,
        headers=headers,
        query_domains=query_domains,
        config_path=config_path,
        mcp_enabled=mcp_enabled,
        mcp_strategy=mcp_strategy,
        mcp_configs=mcp_configs,
        max_search_results=max_search_results,
    )

    report = str(report)
    sanitized = sanitize_filename(f"task_{int(time.time())}_{task}")
    file_paths = await generate_report_files(report, sanitized)
    file_paths["json"] = os.path.relpath(logs_handler.log_file)

    # Broadcast final report text so subscribers can display it
    await broadcast_fn(task_obj, {
        "type": "report",
        "output": report,
    })
    await broadcast_fn(task_obj, {"type": "path", "output": file_paths})

    return file_paths
