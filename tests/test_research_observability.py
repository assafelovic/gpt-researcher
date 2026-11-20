"""Tests for the optional research lifecycle observer."""

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.observability import emit_research_event
from gpt_researcher.scraper.scraper import Scraper
from gpt_researcher.skills.researcher import ResearchConductor


@pytest.mark.asyncio
async def test_observer_accepts_sync_async_and_object_handlers():
    events = []

    def sync_observer(event, **fields):
        events.append((event, fields))

    await emit_research_event(
        sync_observer, "candidate_discovered", url="https://example.test"
    )

    async def async_observer(event, **fields):
        events.append((event, fields))

    await emit_research_event(
        async_observer, "fetch_succeeded", url="https://example.test"
    )

    class ObjectObserver:
        def on_event(self, event, **fields):
            events.append((event, fields))

    await emit_research_event(ObjectObserver(), "selected_for_fetch", position=1)

    assert [event for event, _ in events] == [
        "candidate_discovered",
        "fetch_succeeded",
        "selected_for_fetch",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("observer", [None, lambda *args, **kwargs: None])
async def test_observer_noop_and_success_return_none(observer):
    assert await emit_research_event(observer, "query_planned", position=1) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_observer_failure_is_suppressed(asynchronous):
    if asynchronous:
        async def broken_observer(*args, **kwargs):
            raise RuntimeError("telemetry unavailable")
    else:
        def broken_observer(*args, **kwargs):
            raise RuntimeError("telemetry unavailable")

    await emit_research_event(
        broken_observer, "fetch_failed", url="https://example.test"
    )


def test_public_observer_parameter_is_appended_without_shifting_existing_parameters():
    parameters = list(inspect.signature(GPTResearcher.__init__).parameters)

    assert parameters[-3:] == ["mcp_strategy", "research_observer", "kwargs"]


@pytest.mark.asyncio
async def test_query_planning_emits_queries_in_order():
    events = []

    async def observer(event, **fields):
        events.append((event, fields))

    researcher = SimpleNamespace(
        retrievers=[],
        websocket=None,
        role=None,
        cfg=SimpleNamespace(),
        parent_query="",
        report_type="research_report",
        add_costs=lambda cost: None,
        kwargs={},
        research_observer=observer,
    )
    conductor = ResearchConductor(researcher)

    with (
        patch(
            "gpt_researcher.skills.researcher.plan_research_outline",
            AsyncMock(return_value=["first query", "second query"]),
        ),
        patch(
            "gpt_researcher.skills.researcher.stream_output",
            AsyncMock(),
        ),
    ):
        outline = await conductor.plan_research("question", search_results=[])

    assert outline == ["first query", "second query"]
    assert events == [
        ("query_planned", {"query": "first query", "position": 1}),
        ("query_planned", {"query": "second query", "position": 2}),
    ]


@pytest.mark.asyncio
async def test_scraper_without_observer_preserves_results():
    scraper = Scraper.__new__(Scraper)
    scraper.urls = ["https://good.test", "https://bad.test"]
    scraper.session = object()
    scraper.scraper = "bs"
    scraper.event_handler = None
    scraper.extract_data_from_url = AsyncMock(
        side_effect=[
            {"url": "https://good.test", "raw_content": "usable", "title": "Good"},
            {"url": "https://bad.test", "raw_content": None, "title": "Bad"},
        ]
    )

    retained = await scraper.run()

    assert retained == [
        {"url": "https://good.test", "raw_content": "usable", "title": "Good"}
    ]


@pytest.mark.asyncio
async def test_scraper_emits_before_failed_rows_are_filtered():
    events = []

    async def observer(event, **fields):
        events.append((event, fields))

    scraper = Scraper.__new__(Scraper)
    scraper.urls = ["https://good.test", "https://bad.test"]
    scraper.session = object()
    scraper.scraper = "bs"
    scraper.event_handler = observer
    scraper.extract_data_from_url = AsyncMock(
        side_effect=[
            {"url": "https://good.test", "raw_content": "usable", "title": "Good"},
            {
                "url": "https://bad.test",
                "raw_content": None,
                "title": "Bad",
                "failure_reason": "BACKEND_FAILURE",
            },
        ]
    )

    retained = await scraper.run()

    assert [item["url"] for item in retained] == ["https://good.test"]
    assert [event for event, _ in events] == ["fetch_succeeded", "fetch_failed"]
    assert "reason_code" not in events[0][1]
    assert events[1][1]["reason_code"] == "BACKEND_FAILURE"
    assert all("raw_content" not in fields for _, fields in events)


@pytest.mark.asyncio
async def test_search_emits_candidates_empty_failure_and_deduplication():
    events = []

    class ResultsRetriever:
        requires_scraping = True

        def __init__(self, query, query_domains=None):
            pass

        def search(self, max_results=None):
            return [
                {"href": "https://one.test"},
                {"href": "https://seen.test"},
            ]

    class EmptyRetriever(ResultsRetriever):
        def search(self, max_results=None):
            return []

    class FailedRetriever(ResultsRetriever):
        def search(self, max_results=None):
            raise OSError("provider unavailable")

    async def observer(event, **fields):
        events.append((event, fields))

    researcher = SimpleNamespace(
        retrievers=[ResultsRetriever, EmptyRetriever, FailedRetriever],
        cfg=SimpleNamespace(max_search_results_per_query=5),
        visited_urls={"https://seen.test"},
        verbose=False,
        websocket=None,
        research_observer=observer,
    )

    urls, _ = await ResearchConductor(researcher)._search_relevant_source_urls(
        "query"
    )

    assert urls == ["https://one.test"]
    candidates = [fields for event, fields in events if event == "candidate_discovered"]
    assert [item["rank"] for item in candidates] == [1, 2]
    assert any(event == "search_empty" for event, _ in events)
    failure = next(fields for event, fields in events if event == "search_failed")
    assert failure["reason_code"] == "OSError"
    selected = next(fields for event, fields in events if event == "selected_for_fetch")
    assert "reason_code" not in selected
    deduplicated = next(
        fields for event, fields in events if event == "candidate_deduplicated"
    )
    assert deduplicated["url"] == "https://seen.test"
