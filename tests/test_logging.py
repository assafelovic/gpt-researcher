import pytest
from unittest.mock import AsyncMock
from fastapi import WebSocket
from backend.server import server_utils
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


@pytest.mark.asyncio
async def test_start_command_passes_initialized_logs_handler(
    tmp_path, monkeypatch
):
    mock_websocket = AsyncMock()
    captured = {}

    class FakeManager:
        async def start_streaming(self, *args, **kwargs):
            captured.update(kwargs)
            return "report"

    async def fake_generate_report_files(report, filename):
        return {}

    async def fake_send_file_paths(websocket, file_paths):
        return None

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        server_utils, "generate_report_files", fake_generate_report_files
    )
    monkeypatch.setattr(server_utils, "send_file_paths", fake_send_file_paths)

    command = {
        "task": "test query",
        "report_type": "research_report",
        "source_urls": [],
        "document_urls": [],
        "tone": "Objective",
        "report_source": "web",
    }

    await server_utils.handle_start_command(
        mock_websocket,
        f"start {json.dumps(command)}",
        FakeManager(),
    )

    logs_handler = captured["logs_handler"]
    with open(logs_handler.log_file, "r") as file:
        log_data = json.load(file)

    assert log_data["content"]["query"] == "test query"
