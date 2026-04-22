from unittest.mock import AsyncMock
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from backend.server.server_utils import CustomLogsHandler
from gpt_researcher.mcp.client import MCPClientManager
import json
import asyncio
import glob


def test_custom_logs_handler():
    asyncio.run(_test_custom_logs_handler())


async def _test_custom_logs_handler():
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
    sent_data = mock_websocket.send_json.call_args.args[0]
    assert sent_data["type"] == test_data["type"]
    assert sent_data["message"] == test_data["message"]
    assert sent_data["research_id"] == handler.research_id
    
    # Verify log file contents
    with open(handler.log_file, 'r') as f:
        log_data = json.load(f)
        assert len(log_data['events']) == 1
        assert log_data['events'][0]['data'] == sent_data

def test_content_update():
    asyncio.run(_test_content_update())


async def _test_content_update():
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
    
    sent_data = mock_websocket.send_json.call_args.args[0]
    assert sent_data["research_id"] == handler.research_id
    
    # Verify log file contents
    with open(handler.log_file, 'r') as f:
        log_data = json.load(f)
        assert log_data['content']['query'] == "test query"
        assert log_data['content']['sources'] == ["source1", "source2"]
        assert log_data['content']['report'] == "test report"


def test_log_events_with_content_fields_update_content_section():
    asyncio.run(_test_log_events_with_content_fields_update_content_section())


async def _test_log_events_with_content_fields_update_content_section():
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    handler = CustomLogsHandler(mock_websocket, "startup query")

    await handler.send_json({
        "type": "logs",
        "content": "research_started",
        "query": "startup query",
        "sources": [],
        "context": [],
        "report": "",
    })

    with open(handler.log_file, "r") as f:
        log_data = json.load(f)

    assert log_data["content"]["query"] == "startup query"
    assert len(log_data["events"]) == 1


def test_custom_logs_handler_concurrent_writes_remain_valid_json():
    asyncio.run(_test_custom_logs_handler_concurrent_writes_remain_valid_json())


async def _test_custom_logs_handler_concurrent_writes_remain_valid_json():
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    handler = CustomLogsHandler(mock_websocket, "concurrent query")

    await asyncio.gather(*[
        handler.send_json({
            "type": "logs",
            "message": f"event {i}",
        })
        for i in range(50)
    ])

    with open(handler.log_file, "r") as f:
        log_data = json.load(f)

    assert log_data["research_id"] == handler.research_id
    assert len(log_data["events"]) == 50


def test_custom_logs_handler_preserves_corrupt_log_and_recovers():
    asyncio.run(_test_custom_logs_handler_preserves_corrupt_log_and_recovers())


async def _test_custom_logs_handler_preserves_corrupt_log_and_recovers():
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    handler = CustomLogsHandler(mock_websocket, "corrupt query")

    with open(handler.log_file, "w") as f:
        f.write('{"broken": true}\n{"extra": true}')

    await handler.send_json({"type": "logs", "message": "after corruption"})

    with open(handler.log_file, "r") as f:
        log_data = json.load(f)

    assert log_data["research_id"] == handler.research_id
    assert len(log_data["events"]) == 1
    assert glob.glob(f"{handler.log_file}.corrupt.*")


def test_mcp_client_manager_forwards_streamable_http_headers():
    manager = MCPClientManager([{
        "name": "katailyst",
        "connection_url": "https://katailyst.example/mcp",
        "connection_headers": {"Authorization": "Bearer test-token"},
    }])

    converted = manager.convert_configs_to_langchain_format()

    assert converted["katailyst"]["transport"] == "streamable_http"
    assert converted["katailyst"]["url"] == "https://katailyst.example/mcp"
    assert converted["katailyst"]["headers"] == {"Authorization": "Bearer test-token"}
