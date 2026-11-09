"""MCP research must not run the blocking retriever search on the event loop.

``MCPRetriever.search()`` is the synchronous interface the research pipeline
calls.  It never touches a running loop: it starts its own thread and waits for
it with ``future.result(timeout=300)``, so whoever calls it is stuck for the
whole MCP round (LLM tool selection plus remote tool calls).

``ResearchConductor._execute_mcp_research`` used to call it directly from a
coroutine, which froze the loop for that entire round: websocket log streaming
stopped (the UI looks stuck and shows no progress), and the sibling sub-queries
that ``_get_context_by_web_search`` gathers could not make progress, so N
searches cost the sum of their durations instead of the longest one.

Every other retriever call site already offloads the blocking search to a
worker thread for exactly this reason -- see
``actions/query_processing.get_search_results`` ("Retriever searches are
blocking HTTP calls; keep the event loop free") and
``_search_relevant_source_urls``.
"""

import asyncio
import contextlib
import threading
import time
from types import SimpleNamespace

import pytest

from gpt_researcher.skills.researcher import ResearchConductor

SEARCH_SECONDS = 0.4
POLL_SECONDS = 0.02
EXPECTED_RESULTS = [{"title": "T", "href": "https://example.com/mcp", "body": "B" * 50}]


def make_researcher(max_search_results_per_query=7):
    return SimpleNamespace(
        retrievers=[],
        cfg=SimpleNamespace(max_search_results_per_query=max_search_results_per_query),
        headers={},
        query_domains=[],
        websocket=None,
        verbose=False,
        mcp_configs=[{"name": "search"}],
        mcp_strategy="fast",
    )


def make_retriever(state):
    """A retriever shaped like ``MCPRetriever``: sync ``search`` that blocks."""

    class BlockingMCPRetriever:
        def __init__(self, query, headers=None, query_domains=None, websocket=None, researcher=None):
            state["query"] = query

        def search(self, max_results=10):
            state["thread_id"] = threading.get_ident()
            state["max_results"] = max_results
            time.sleep(SEARCH_SECONDS)
            return list(EXPECTED_RESULTS)

    BlockingMCPRetriever.__name__ = "MCPRetriever"
    return BlockingMCPRetriever


@pytest.mark.asyncio
async def test_mcp_search_runs_off_the_event_loop_thread():
    """The blocking search must run in a worker thread, not the loop's own."""
    loop_thread_id = threading.get_ident()
    state = {}
    conductor = ResearchConductor(make_researcher())

    results = await conductor._execute_mcp_research(make_retriever(state), "query")

    assert results == EXPECTED_RESULTS
    assert state["max_results"] == 7, "max_results must still reach the retriever"
    assert state["thread_id"] != loop_thread_id


@pytest.mark.asyncio
async def test_mcp_search_does_not_stall_the_event_loop():
    """Coroutines keep running while a slow MCP search is in flight."""
    state = {}
    conductor = ResearchConductor(make_researcher())
    ticks = 0

    async def poll():
        nonlocal ticks
        while True:
            await asyncio.sleep(POLL_SECONDS)
            ticks += 1

    poller = asyncio.create_task(poll())
    await asyncio.sleep(0)  # arm the poller before the search starts

    results = await conductor._execute_mcp_research(make_retriever(state), "query")

    poller.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await poller

    assert results == EXPECTED_RESULTS
    # SEARCH_SECONDS / POLL_SECONDS is 20 on a quiet loop; a blocked loop
    # yields 0. Five leaves room for a slow or loaded CI machine.
    assert ticks >= 5, f"event loop was blocked during the MCP search ({ticks} ticks)"
