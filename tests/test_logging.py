import pytest
from unittest.mock import AsyncMock
from fastapi import WebSocket
from backend.server.server_utils import CustomLogsHandler
import os
import json

@pytest.mark.asyncio
async def test_custom_logs_handler():
    # Mock websocket
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Test initialization
    handler = CustomLogsHandler(mock_websocket, "test_query")
    
    # Verify log file creation
    assert os.path.exists(handler.log_file)
    
    # Test sending log data
    test_data = {
        "type": "logs",
        "message": "Test log message"
    }
    
    await handler.send_json(test_data)
    
    # Verify websocket was called with correct data
    mock_websocket.send_json.assert_called_once_with(test_data)
    
    # Verify log file contents
    with open(handler.log_file, 'r') as f:
        log_data = json.load(f)
        assert len(log_data['events']) == 1
        assert log_data['events'][0]['data'] == test_data 

@pytest.mark.asyncio
async def test_content_update():
    """Test handling of non-log type data that updates content"""
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    handler = CustomLogsHandler(mock_websocket, "test_query")
    
    # Test content update
    content_data = {
        "query": "test query",
        "sources": ["source1", "source2"],
        "report": "test report"
    }
    
    await handler.send_json(content_data)
    
    mock_websocket.send_json.assert_called_once_with(content_data)
    
    # Verify log file contents
    with open(handler.log_file, 'r') as f:
        log_data = json.load(f)
        assert log_data['content']['query'] == "test query"
        assert log_data['content']['sources'] == ["source1", "source2"]
        assert log_data['content']['report'] == "test report"