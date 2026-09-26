"""Deep research preserves accumulated state when query generation returns no queries."""

from types import SimpleNamespace

import pytest

from gpt_researcher.skills.deep_research import DeepResearchSkill


@pytest.mark.asyncio
async def test_zero_queries_preserve_accumulated_state():
    researcher = SimpleNamespace(
        cfg=SimpleNamespace(
            deep_research_breadth=3,
            deep_research_depth=2,
            deep_research_concurrency=2,
            strategic_llm_provider="openai",
            strategic_llm_model="gpt",
            reasoning_effort=None,
            config_path=None,
        ),
        websocket=None,
        tone=None,
        headers={},
        visited_urls=set(),
    )
    skill = DeepResearchSkill(researcher)

    async def fake_generate(query, num_queries=3):
        return []

    skill.generate_search_queries = fake_generate  # type: ignore

    learnings = ["existing learning"]
    citations = {"existing learning": "https://example.com/source"}
    visited_urls = {"https://example.com/source"}

    result = await skill.deep_research(
        query="topic",
        breadth=3,
        depth=2,
        learnings=learnings,
        citations=citations,
        visited_urls=visited_urls,
    )

    assert result == {
        "learnings": learnings,
        "visited_urls": visited_urls,
        "citations": citations,
        "context": [],
        "sources": [],
    }
    assert skill.context == []
    assert skill.research_sources == []
