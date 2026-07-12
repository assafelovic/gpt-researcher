"""Empty-context guard for ReportGenerator (#1572)."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from gpt_researcher.skills.writer import ReportGenerator


def _make_generator(context):
    researcher = SimpleNamespace(
        query="What is ZZZnotareal topic?",
        context=context,
        verbose=False,
        websocket=None,
        report_type="research_report",
        role="researcher",
        cfg=SimpleNamespace(agent_role=None),
        headers={},
        kwargs={},
        get_research_images=lambda: [],
        parent_query="",
        add_costs=lambda *a, **k: None,
        tone=None,
        report_source="web",
    )
    return ReportGenerator(researcher)


@pytest.mark.asyncio
async def test_empty_string_context_skips_llm(monkeypatch):
    gen = _make_generator("")
    called = {"n": 0}

    async def boom(**kwargs):
        called["n"] += 1
        raise AssertionError("generate_report should not be called")

    monkeypatch.setattr(
        "gpt_researcher.skills.writer.generate_report", boom
    )
    report = await gen.write_report()
    assert "No Relevant Sources Found" in report
    assert called["n"] == 0


@pytest.mark.asyncio
async def test_empty_list_context_skips_llm(monkeypatch):
    gen = _make_generator([])
    called = {"n": 0}

    async def boom(**kwargs):
        called["n"] += 1
        raise AssertionError("generate_report should not be called")

    monkeypatch.setattr(
        "gpt_researcher.skills.writer.generate_report", boom
    )
    report = await gen.write_report()
    assert "No Relevant Sources Found" in report
    assert called["n"] == 0


@pytest.mark.asyncio
async def test_nonempty_context_still_calls_generate(monkeypatch):
    gen = _make_generator(["real source for the query"])
    called = {"n": 0}

    async def fake_generate(**kwargs):
        called["n"] += 1
        return "ok report"

    monkeypatch.setattr(
        "gpt_researcher.skills.writer.generate_report", fake_generate
    )
    report = await gen.write_report()
    assert report == "ok report"
    assert called["n"] == 1
