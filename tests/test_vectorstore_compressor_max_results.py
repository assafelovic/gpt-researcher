"""Regression: ``VectorstoreCompressor`` must honour its ``max_results``.

The constructor accepts ``max_results`` and documents it as "Maximum number of
results to return", but ``async_get_context`` declared its own
``max_results: int = 5`` default and never looked at ``self.max_results``: a
compressor built with ``max_results=7`` still asked the vector store for five
documents, and the configured limit was silently ignored for every caller that
relies on the documented default.
"""

import pytest

from gpt_researcher.context.compression import VectorstoreCompressor


class _RecordingStore:
    """Vector store double that records the arguments of the similarity search."""

    def __init__(self):
        self.calls = []

    async def asimilarity_search(self, query, k, filter):
        self.calls.append({"query": query, "k": k, "filter": filter})
        return []


@pytest.mark.asyncio
async def test_configured_max_results_is_the_default():
    store = _RecordingStore()
    compressor = VectorstoreCompressor(store, max_results=7, filter={"source": "a.example"})

    await compressor.async_get_context("ev market share")

    assert store.calls == [
        {"query": "ev market share", "k": 7, "filter": {"source": "a.example"}}
    ]


@pytest.mark.asyncio
async def test_explicit_max_results_still_wins():
    store = _RecordingStore()
    compressor = VectorstoreCompressor(store, max_results=7)

    await compressor.async_get_context("ev market share", max_results=3)

    assert store.calls == [{"query": "ev market share", "k": 3, "filter": None}]
