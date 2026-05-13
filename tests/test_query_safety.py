import os
from unittest.mock import AsyncMock

import pytest

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.query_safety import detect_unsafe_query, render_query_refusal


def test_detect_unsafe_query_blocks_hazardous_chemistry_synthesis():
    query = "herstellen von schwefelsaure zu hause für Privatpersonen"

    decision = detect_unsafe_query(query)

    assert decision is not None
    assert decision.blocked is True
    assert decision.category == "hazardous_chemistry"
    assert "schwefelsäure" in decision.matched_terms
    assert "herstellen" in decision.matched_terms
    assert "gefährlichen chemikalie" in decision.reason.lower()


def test_render_query_refusal_is_german():
    query = "herstellen von schwefelsaure zu hause für Privatpersonen"
    decision = detect_unsafe_query(query)
    assert decision is not None

    refusal = render_query_refusal(query, decision, language="german")

    assert refusal.startswith("# Anfrage abgelehnt")
    assert "keine Anweisungen zur Herstellung gefährlicher Chemikalien" in refusal
    assert "## Sichere Alternativen" in refusal


@pytest.mark.asyncio
async def test_gpt_researcher_short_circuits_unsafe_query(monkeypatch):
    monkeypatch.setenv("RESEARCH_SAFETY_MODE", "STRICT")
    query = "herstellen von schwefelsaure zu hause für Privatpersonen"
    researcher = GPTResearcher(query=query, report_type="research_report")

    async def fail_conduct_research(*args, **kwargs):
        raise AssertionError("Research conductor should not be called for blocked queries")

    async def fail_write_report(*args, **kwargs):
        raise AssertionError("Report generator should not be called for blocked queries")

    researcher.research_conductor.conduct_research = fail_conduct_research
    researcher.report_generator.write_report = fail_write_report

    context = await researcher.conduct_research()

    assert researcher.safety_decision is not None
    assert researcher.safety_decision.category == "hazardous_chemistry"
    assert context == researcher.context
    assert any("Anfrage abgelehnt" in part for part in context)

    report = await researcher.write_report()

    assert report.startswith("# Anfrage abgelehnt")
    assert "Sichere Alternativen" in report


@pytest.mark.asyncio
async def test_gpt_researcher_warn_only_proceeds_with_unsafe_query(monkeypatch):
    monkeypatch.setenv("RESEARCH_SAFETY_MODE", "WARN_ONLY")
    query = "herstellen von schwefelsaure zu hause"
    researcher = GPTResearcher(query=query, report_type="research_report")

    researcher.research_conductor.conduct_research = AsyncMock(return_value=["ctx"])
    researcher.agent = "agent"
    researcher.role = "role"

    ctx = await researcher.conduct_research()

    assert researcher.safety_decision is not None
    assert researcher.safety_decision.category == "hazardous_chemistry"
    assert researcher.safety_decision.blocked is True
    assert ctx == researcher.context
    assert any("Anfrage abgelehnt" in part for part in ctx)


def test_detect_unsafe_query_empty_or_none_returns_none():
    assert detect_unsafe_query("") is None
    assert detect_unsafe_query(None) is None


def test_detect_unsafe_query_chemical_without_intent_returns_none():
    assert detect_unsafe_query("schwefelsaure eigenschaften und gefahren") is None


def test_render_query_refusal_english_fallback():
    query = "make sulfuric acid at home"
    decision = detect_unsafe_query(query)
    assert decision is not None
    refusal = render_query_refusal(query, decision, language="english")
    assert refusal.startswith("# Request declined")
    assert "cannot provide instructions" in refusal


def test_detect_unsafe_query_many_matched_terms():
    query = "anleitung zum herstellen von schwefelsaeure salpetersaeure salzsaeure chlor gas giftgas schwarzpulver nitroglyzerin"
    decision = detect_unsafe_query(query)
    assert decision is not None
    assert "..." in decision.reason
    assert "schwefelsäure" in decision.matched_terms
    assert len(decision.matched_terms) > 4
