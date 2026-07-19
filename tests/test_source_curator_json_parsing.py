"""Regression: SourceCurator must recover fenced/malformed LLM JSON.

Models routinely wrap their JSON in ```json fences despite the curator
prompt's "no markdown" instruction. Plain ``json.loads`` raises on that
output, which sent ``curate_sources`` down its except-branch and silently
returned the *full uncurated* source set — defeating the curation the user
opted into via ``cfg.curate_sources``. The parser now matches the rest of
the codebase (``parse_json_markdown`` + ``json_repair``), so a
well-formed-but-fenced response is parsed instead of discarded.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from gpt_researcher.skills.curator import SourceCurator


def _fake_researcher():
    """Minimal researcher stub exercising only what curate_sources reads."""
    return SimpleNamespace(
        verbose=False,
        websocket=None,
        role="system role",
        query="market share of EVs",
        cfg=SimpleNamespace(
            smart_llm_model="openai:gpt-x",
            smart_llm_provider="openai",
            llm_kwargs={},
        ),
        prompt_family=SimpleNamespace(curate_sources=lambda *a, **k: "curate prompt"),
        add_costs=lambda *a, **k: None,
    )


SOURCES = [
    {"Title": "A", "Content": "a", "Source": "https://a.example"},
    {"Title": "B", "Content": "b", "Source": "https://b.example"},
    {"Title": "C", "Content": "c", "Source": "https://c.example"},
]


@pytest.mark.asyncio
async def test_markdown_fenced_response_is_parsed_not_dropped(monkeypatch):
    fenced = (
        "```json\n"
        '[{"Title": "A", "Content": "a", "Source": "https://a.example"}]\n'
        "```"
    )
    monkeypatch.setattr(
        "gpt_researcher.skills.curator.create_chat_completion",
        AsyncMock(return_value=fenced),
    )

    result = await SourceCurator(_fake_researcher()).curate_sources(SOURCES)

    # Curation succeeded: the single ranked source, NOT the 3 uncurated ones.
    assert isinstance(result, list) and len(result) == 1
    assert result[0]["Source"] == "https://a.example"
    assert result is not SOURCES


@pytest.mark.asyncio
async def test_clean_unfenced_response_still_parses(monkeypatch):
    clean = '[{"Title": "B", "Content": "b", "Source": "https://b.example"}]'
    monkeypatch.setattr(
        "gpt_researcher.skills.curator.create_chat_completion",
        AsyncMock(return_value=clean),
    )

    result = await SourceCurator(_fake_researcher()).curate_sources(SOURCES)

    assert isinstance(result, list) and len(result) == 1
    assert result[0]["Source"] == "https://b.example"


@pytest.mark.asyncio
async def test_non_list_response_falls_back_to_uncurated(monkeypatch):
    # A non-list result (json_repair returns "" / a dict for unusable output
    # instead of raising) must NOT be treated as a curation result — the
    # existing safety net that returns the uncurated sources must still fire.
    monkeypatch.setattr(
        "gpt_researcher.skills.curator.create_chat_completion",
        AsyncMock(return_value='{"not": "a list"}'),
    )

    result = await SourceCurator(_fake_researcher()).curate_sources(SOURCES)

    assert result is SOURCES
