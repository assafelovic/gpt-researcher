#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from dotenv import load_dotenv

if TYPE_CHECKING:
    import logging

    from fastapi import WebSocket as ServerWebSocket
    from gpt_researcher.utils.enum import Tone

from gpt_researcher.utils.logger import get_formatted_logger

logger: logging.Logger = get_formatted_logger(__name__)

try:
    from backend.server.server_utils import CustomLogsHandler  # noqa: E402
except ImportError:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, path)
    from backend.server.server_utils import CustomLogsHandler  # noqa: E402

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()


def open_task() -> dict[str, Any]:
    # Construct the absolute path to task.json
    task_json_path: Path = Path(os.path.normpath(os.path.abspath(__file__))).parent.joinpath("task.json")
    task: dict[str, Any] = json.loads(task_json_path.read_text())
    logger.debug("task:", repr(task))

    if not task or not task_json_path.exists() or not task_json_path.is_file() or not isinstance(task, dict) or not task.get("query") or not str(task.get("query")).strip():
        raise RuntimeError("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    return task


async def run_research_task(
    query: str,
    websocket: CustomLogsHandler | ServerWebSocket | None = None,
    stream_output: Callable[
        [str, str, str, ServerWebSocket | CustomLogsHandler | None],
        Coroutine[Any, Any, Any],
    ]
    | None = None,
    tone: Tone | str | None = None,
    headers: dict[str, Any] | None = None,
) -> str:
    from multi_agents.agents import ChiefEditorAgent

    task: dict[str, Any] = open_task()
    task["query"] = query

    chief_editor = ChiefEditorAgent(
        task,
        (websocket.websocket if isinstance(websocket, CustomLogsHandler) else websocket),
        stream_output,
        tone,
        headers,
    )
    research_report: str = await chief_editor.run_research_task(task_id=uuid.uuid4().int)

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report


async def main() -> str:
    from multi_agents.agents import ChiefEditorAgent

    task: dict[str, Any] = open_task()

    chief_editor = ChiefEditorAgent(task)
    research_report: str = await chief_editor.run_research_task(task_id=uuid.uuid4().int)

    return research_report


if __name__ == "__main__":
    asyncio.run(main())
