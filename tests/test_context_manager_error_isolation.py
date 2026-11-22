"""One failing written-content query must not abort its sibling queries.

`get_similar_written_contents_by_draft_section_titles` fans a subtopic's
draft section titles out to concurrent compression queries. A transient
embeddings failure inside one query used to propagate out of the gather
and kill the whole detailed-report write phase, after all research and
writing had already been paid for. The per-query contract mirrors the
embeddings-unavailable fallback already used in
`__get_similar_written_contents_by_query`: degrade to lexical ranking.
"""

import asyncio

import pytest
from langchain_core.embeddings import Embeddings

from gpt_researcher.context import compression
from gpt_researcher.context.compression import WrittenContentCompressor
from gpt_researcher.skills import context_manager
from gpt_researcher.skills.context_manager import ContextManager


@pytest.fixture(autouse=True)
def _offline_cost_estimate(monkeypatch):
    # The real estimate downloads a tiktoken encoding; offline it raises and the
    # fallback under test would silently absorb it. :-)
    monkeypatch.setattr(compression, "estimate_embedding_cost", lambda **kwargs: 0.0)


def _count_fallbacks(monkeypatch):
    calls = []
    real = context_manager.rank_written_sections

    def counting(*args, **kwargs):
        calls.append(args[0])
        return real(*args, **kwargs)

    monkeypatch.setattr(context_manager, "rank_written_sections", counting)
    return calls


class HashingEmbeddings(Embeddings):
    """Deterministic hashed bag-of-words vectors, no model, key or network."""

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * 64
        for token in text.lower().split():
            vec[hash(token) % 64] += 1.0
        return vec

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


BATTERY_CONTENT = (
    "solid state batteries cost about $400 per kwh in 2026 and keep falling " * 40
)
GRID_CONTENT = (
    "interconnection queues delayed the solar farm for several years " * 40
)

SECTIONS = [
    {"section_title": "Battery costs", "written_content": BATTERY_CONTENT},
    {"section_title": "Grid interconnection backlog", "written_content": GRID_CONTENT},
]

FAILING_QUERY = "battery recycling hazards"


class _FakeMemory:
    def get_embeddings(self):
        return HashingEmbeddings()


class _FakeResearcher:
    """Only the attributes ContextManager touches on this path."""

    verbose = False
    kwargs = {}
    memory = _FakeMemory()

    def add_costs(self, cost):
        pass


def _patch_flaky_compressor(monkeypatch):
    """Make the compressor raise only for the poisoned query."""
    real_async_get_context = WrittenContentCompressor.async_get_context

    async def flaky(self, query, max_results=5, cost_callback=None):
        if FAILING_QUERY in query:
            raise RuntimeError("transient embedding provider failure")
        return await real_async_get_context(
            self, query, max_results=max_results, cost_callback=cost_callback
        )

    monkeypatch.setattr(WrittenContentCompressor, "async_get_context", flaky)


def test_all_queries_succeed_returns_their_sections(monkeypatch):
    fallbacks = _count_fallbacks(monkeypatch)
    manager = ContextManager(_FakeResearcher())
    results = asyncio.run(
        manager.get_similar_written_contents_by_draft_section_titles(
            "Solid-state batteries",
            ["solid state batteries cost per kwh in 2026", FAILING_QUERY],
            SECTIONS,
        )
    )
    assert isinstance(results, list) and results
    assert any("Battery costs" in r for r in results)
    assert fallbacks == []


def test_failing_written_content_query_degrades_instead_of_aborting(monkeypatch):
    _patch_flaky_compressor(monkeypatch)
    fallbacks = _count_fallbacks(monkeypatch)
    manager = ContextManager(_FakeResearcher())
    results = asyncio.run(
        manager.get_similar_written_contents_by_draft_section_titles(
            "Solid-state batteries",
            ["solid state batteries cost per kwh in 2026", FAILING_QUERY],
            SECTIONS,
        )
    )
    assert isinstance(results, list) and results
    assert any("Battery costs" in r for r in results)
    assert fallbacks == [FAILING_QUERY]
