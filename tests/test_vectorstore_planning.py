"""Vector-store research can plan and retrieve without a web-search provider."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import pytest

from gpt_researcher.skills import researcher as researcher_module
from gpt_researcher.skills.researcher import ResearchConductor


@pytest.mark.asyncio
async def test_vectorstore_research_does_not_require_web_search(monkeypatch):
    web_queries = []

    class UnconfiguredWebRetriever:
        def __init__(self, query, query_domains=None):
            web_queries.append(query)
            raise ValueError("Web search API key is not configured")

    vector_filter = {"collection": "internal"}
    retrieve = AsyncMock(side_effect=lambda query, _filter: f"Stored evidence for {query}")
    researcher = SimpleNamespace(
        query="original question",
        verbose=False,
        websocket=None,
        agent="agent",
        role="research role",
        source_urls=None,
        report_source="langchain_vectorstore",
        report_type="research_report",
        cfg=SimpleNamespace(curate_sources=False, max_search_results_per_query=5),
        retrievers=[UnconfiguredWebRetriever],
        vector_store_filter=vector_filter,
        parent_query="",
        kwargs={},
        add_costs=lambda *_: None,
        context_manager=SimpleNamespace(
            get_similar_content_by_query_with_vectorstore=retrieve,
        ),
    )
    plan = AsyncMock(return_value=["targeted query"])
    monkeypatch.setattr(researcher_module, "plan_research_outline", plan)
    monkeypatch.setattr(researcher_module, "stream_output", AsyncMock())

    context = await ResearchConductor(researcher).conduct_research()

    assert web_queries == []
    assert plan.await_args.kwargs["search_results"] == []
    assert retrieve.await_args_list == [
        call("targeted query", vector_filter),
        call("original question", vector_filter),
    ]
    assert context == [
        "Stored evidence for targeted query",
        "Stored evidence for original question",
    ]
