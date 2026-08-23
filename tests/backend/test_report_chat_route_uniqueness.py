"""POST /api/reports/{id}/chat must be a single LLM-backed handler (#1979)."""

import importlib
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORT_STORE_PATH", str(tmp_path / "reports.json"))
    # Avoid StaticFiles path errors if frontend layout differs in CI
    frontend = REPO_ROOT / "frontend"
    if not frontend.exists():
        (tmp_path / "frontend" / "static").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

    # Import app module fresh enough to use ReportStore path env
    if "server.app" in sys.modules:
        del sys.modules["server.app"]
    mod = importlib.import_module("server.app")
    return mod


def test_single_post_report_chat_route(app_module):
    paths = [
        (getattr(r, "methods", None) or set(), getattr(r, "path", None))
        for r in app_module.app.routes
    ]
    post_chat = [
        (methods, path)
        for methods, path in paths
        if path == "/api/reports/{research_id}/chat" and methods and "POST" in methods
    ]
    assert len(post_chat) == 1

    put_routes = [
        (methods, path)
        for methods, path in paths
        if path == "/api/reports/{research_id}" and methods and "PUT" in methods
    ]
    delete_routes = [
        (methods, path)
        for methods, path in paths
        if path == "/api/reports/{research_id}" and methods and "DELETE" in methods
    ]
    assert len(put_routes) == 1
    assert len(delete_routes) == 1


@pytest.mark.asyncio
async def test_report_chat_runs_llm_and_persists(app_module):
    stored = {
        "id": "r1",
        "answer": "Report body about widgets.",
        "chatMessages": [],
        "timestamp": 1,
    }

    async def get_report(rid):
        return stored if rid == "r1" else None

    async def upsert(rid, report):
        nonlocal stored
        stored = report

    class FakeRequest:
        async def json(self):
            return {"role": "user", "content": "What is this about?"}

    with (
        patch.object(app_module.report_store, "get_report", side_effect=get_report),
        patch.object(app_module.report_store, "upsert_report", side_effect=upsert),
        patch.object(
            app_module,
            "ChatAgentWithMemory",
        ) as ChatCls,
    ):
        agent = ChatCls.return_value
        agent.chat = AsyncMock(return_value=("Widgets summary.", None))
        result = await app_module.research_report_chat("r1", FakeRequest())

    assert result["success"] is True
    assert result["response"]["role"] == "assistant"
    assert result["response"]["content"] == "Widgets summary."
    assert any(m.get("role") == "user" for m in stored["chatMessages"])
    assert stored["chatMessages"][-1]["role"] == "assistant"
    ChatCls.assert_called_once()
    agent.chat.assert_awaited_once()
