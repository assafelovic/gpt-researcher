import pytest
import asyncio
from pathlib import Path
import json
import logging
from fastapi import WebSocket
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestWebSocket(WebSocket):
    def __init__(self):
        self.events = []
        self.scope = {}

    def __bool__(self):
        return True

    async def accept(self):
        self.scope["type"] = "websocket"
        pass
        
    async def send_json(self, event):
        logger.info(f"WebSocket received event: {event}")
        self.events.append(event)

@pytest.mark.asyncio
async def test_log_output_file():
    """Test to verify logs are properly written to output file"""
    from gpt_researcher.agent import GPTResearcher
    from backend.server.server_utils import CustomLogsHandler
    
    # 1. Setup like the main app
    websocket = TestWebSocket()
    await websocket.accept()
    
    # 2. Initialize researcher like main app
    query = "What is the capital of France?"
    research_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query)}"
    logs_handler = CustomLogsHandler(websocket=websocket, task=research_id)
    researcher = GPTResearcher(query=query, websocket=logs_handler)
    
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
        assert len(data.get('events', [])) > 0, "No events in output file" 

    # Clean up the output files
    for output_file in output_files:
        output_file.unlink()
        logger.info(f"Deleted output file: {output_file}")