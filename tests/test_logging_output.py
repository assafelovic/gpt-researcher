import pytest
import asyncio
from pathlib import Path
import json
import logging
from fastapi import WebSocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestWebSocket(WebSocket):
    def __init__(self):
        self.events = []
        
    async def accept(self):
        pass
        
    async def send_json(self, event):
        logger.info(f"WebSocket received event: {event}")
        self.events.append(event)

@pytest.mark.asyncio
async def test_log_output_file():
    """Test to verify logs are properly written to output file"""
    from gpt_researcher.agent import GPTResearcher
    
    # 1. Setup like the main app
    websocket = TestWebSocket()
    await websocket.accept()
    
    # 2. Initialize researcher like main app
    query = "What is the capital of France?"
    researcher = GPTResearcher(query=query, websocket=websocket)
    
    # 3. Run research
    await researcher.conduct_research()
    
    # 4. Verify events were captured
    logger.info(f"Events captured: {len(websocket.events)}")
    assert len(websocket.events) > 0, "No events were captured"
    
    # 5. Check output file
    output_dir = Path("outputs")
    output_files = list(output_dir.glob(f"task_*_{query.replace(' ', '_')[:50]}.json"))
    assert len(output_files) > 0, "No output file was created"
    
    with open(output_files[-1]) as f:
        data = json.load(f)
        assert len(data.get('events', [])) > 0, "No events in output file" 