"""RESTRICT_CLIENT_MCP_STDIO: opt-in filter for client-supplied stdio MCP servers.

No process is started: the research manager is an autospec mock, and
MCPClientManager.convert_configs_to_langchain_format() only builds dictionaries.
"""

import asyncio
import inspect
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, create_autospec

import pytest

from backend.server import server_utils
from backend.server.websocket_manager import WebSocketManager
from gpt_researcher.mcp.client import MCPClientManager

PLACEHOLDER = "fixture-command-placeholder"

# Client payloads that the MCP converter maps to the stdio transport.
STDIO_BOUND_CONFIGS = {
    "command-only": [
        {"name": "fixture", "command": PLACEHOLDER, "args": ["--fixture-arg"], "env": {"FIXTURE": "1"}}
    ],
    "explicit-stdio-type": [
        {"name": "fixture", "connection_type": "stdio", "command": PLACEHOLDER}
    ],
    "non-network-url": [
        {"name": "fixture", "connection_url": "fixture-scheme:run", "command": PLACEHOLDER}
    ],
}


def _forwarded_mcp_configs(monkeypatch, tmp_path, mcp_configs):
    """Run handle_start_command with a mocked manager and return the forwarded mcp_configs."""
    monkeypatch.chdir(tmp_path)  # CustomLogsHandler writes its log file below the cwd
    monkeypatch.setattr(server_utils, "generate_report_files", AsyncMock(return_value={}))
    websocket = SimpleNamespace(send_json=AsyncMock())
    manager = create_autospec(WebSocketManager, instance=True)
    manager.start_streaming.return_value = "fixture report"
    frame = "start " + json.dumps(
        {
            "task": "fixture task",
            "report_type": "research_report",
            "report_source": "web",
            "tone": "Objective",
            "mcp_enabled": True,
            "mcp_strategy": "fast",
            "mcp_configs": mcp_configs,
        }
    )

    asyncio.run(server_utils.handle_start_command(websocket, frame, manager))

    manager.start_streaming.assert_awaited_once()
    call = manager.start_streaming.await_args
    bound = inspect.signature(WebSocketManager.start_streaming).bind(manager, *call.args, **call.kwargs)
    bound.apply_defaults()
    return bound.arguments["mcp_configs"] or []


@pytest.mark.parametrize("flag", [None, "false", "0"], ids=["unset", "false", "0"])
def test_default_keeps_client_mcp_configs_unchanged(monkeypatch, tmp_path, flag):
    if flag is None:
        monkeypatch.delenv("RESTRICT_CLIENT_MCP_STDIO", raising=False)
    else:
        monkeypatch.setenv("RESTRICT_CLIENT_MCP_STDIO", flag)
    configs = STDIO_BOUND_CONFIGS["command-only"]

    assert _forwarded_mcp_configs(monkeypatch, tmp_path, configs) == configs


@pytest.mark.parametrize("mcp_configs", list(STDIO_BOUND_CONFIGS.values()), ids=list(STDIO_BOUND_CONFIGS))
def test_restriction_drops_stdio_bound_configs(monkeypatch, tmp_path, mcp_configs):
    monkeypatch.setenv("RESTRICT_CLIENT_MCP_STDIO", "true")

    forwarded = _forwarded_mcp_configs(monkeypatch, tmp_path, mcp_configs)

    converted = MCPClientManager(forwarded).convert_configs_to_langchain_format()
    assert not any(cfg.get("transport") == "stdio" for cfg in converted.values()), converted
    assert PLACEHOLDER not in json.dumps(forwarded)


def test_restriction_keeps_network_configs(monkeypatch, tmp_path):
    monkeypatch.setenv("RESTRICT_CLIENT_MCP_STDIO", "true")
    network = {"name": "remote", "connection_url": "https://fixture.invalid/mcp"}
    with_command = {"name": "remote-2", "connection_url": "wss://fixture.invalid/mcp", "command": PLACEHOLDER}

    forwarded = _forwarded_mcp_configs(monkeypatch, tmp_path, [network, with_command])

    assert forwarded == [network, with_command]
    converted = MCPClientManager(forwarded).convert_configs_to_langchain_format()
    assert converted["remote"]["transport"] == "streamable_http"
    assert converted["remote-2"]["transport"] == "websocket"
    assert all("command" not in cfg for cfg in converted.values())
