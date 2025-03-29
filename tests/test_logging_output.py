from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import WebSocket

logging.basicConfig(level=logging.INFO)
from gpt_researcher.utils.logger import get_formatted_logger

logger: logging.Logger = get_formatted_logger(__name__)


class TestWebSocket(WebSocket):
    def __init__(self):
        self.events: list[dict[str, Any]] = []
        self.scope: dict[str, Any] = {}

    def __bool__(self):
        return True

    async def accept(self):
        self.scope["type"] = "websocket"
        pass

    async def send_json(self, event: dict[str, Any]):
        logger.info(f"WebSocket received event: {event}")
        self.events.append(event)


@pytest.mark.asyncio
async def test_log_output_file():
    """Test to verify logs are properly written to output file."""
    from backend.server.server_utils import CustomLogsHandler
    from gpt_researcher.agent import GPTResearcher

    # 1. Setup like the main app
    websocket = TestWebSocket()
    await websocket.accept()

    # 2. Initialize researcher like main app
    query = "What is the capital of France?"
    research_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query)}"
    logs_handler = CustomLogsHandler(websocket=websocket, task=research_id)
    researcher = GPTResearcher(
        query=query, websocket=websocket, research_id=research_id
    )
    # 3. Run research
    await researcher.conduct_research()

    # 4. Verify events were captured
    logger.info(f"Events captured: {len(websocket.events)}")
    assert len(websocket.events) > 0, "No events were captured"

    # 5. Check output file
    output_dir = Path().joinpath(Path.cwd(), "outputs")
    output_files = list(output_dir.glob(f"task_*{research_id}*.json"))
    assert len(output_files) > 0, "No output file was created"

    with open(output_files[-1]) as f:
        data = json.load(f)
        assert len(data.get("events", [])) > 0, "No events in output file"

    # Clean up the output files
    for output_file in output_files:
        output_file.unlink()
        logger.info(f"Deleted output file: {output_file}")
