import importlib
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_websocket_manager_module_imports():
    module = importlib.import_module("backend.server.websocket_manager")
    assert hasattr(module, "WebSocketManager")


def test_server_app_module_imports():
    module = importlib.import_module("backend.server.app")
    assert hasattr(module, "app")


@pytest.mark.asyncio
async def test_start_streaming_uses_config_path_from_env(monkeypatch):
    module = importlib.import_module("backend.server.websocket_manager")
    captured = {}

    async def fake_run_agent(
        task,
        report_type,
        report_source,
        source_urls,
        document_urls,
        tone,
        websocket,
        stream_output=module.stream_output,
        headers=None,
        query_domains=None,
        config_path="",
        return_researcher=False,
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=None,
        max_search_results=None,
    ):
        captured["task"] = task
        captured["report_type"] = report_type
        captured["report_source"] = report_source
        captured["tone"] = tone.name
        captured["config_path"] = config_path
        return "ok"

    monkeypatch.setenv("CONFIG_PATH", "test-config")
    monkeypatch.setattr(module, "run_agent", fake_run_agent)

    manager = module.WebSocketManager()
    result = await manager.start_streaming(
        task="research task",
        report_type="research_report",
        report_source="web",
        source_urls=[],
        document_urls=[],
        tone="Objective",
        websocket=None,
    )

    assert result == "ok"
    assert captured["task"] == "research task"
    assert captured["report_type"] == "research_report"
    assert captured["report_source"] == "web"
    assert captured["tone"] == "Objective"
    assert captured["config_path"] == "test-config"
