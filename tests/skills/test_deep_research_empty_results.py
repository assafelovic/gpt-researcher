"""Deep research terminates when a level yields no results (#1579)."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gpt_researcher.skills.deep_research import DeepResearchSkill


@pytest.mark.asyncio
async def test_stops_when_all_query_processors_return_none():
    researcher = SimpleNamespace(
        cfg=SimpleNamespace(
            deep_research_breadth=2,
            deep_research_depth=3,
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
        mcp_configs=None,
        mcp_strategy=None,
    )
    skill = DeepResearchSkill(researcher)

    async def fake_generate(query, num_queries=3):
        return [
            {"query": "q1", "researchGoal": "g1"},
            {"query": "q2", "researchGoal": "g2"},
        ]

    # Force every process_query path to fail by making nested research raise
    async def boom(*a, **k):
        raise RuntimeError("retriever misconfigured")

    skill.generate_search_queries = fake_generate  # type: ignore

    with patch("gpt_researcher.GPTResearcher") as MockR:
        inst = MockR.return_value
        inst.conduct_research = AsyncMock(side_effect=boom)
        inst.visited_urls = set()
        inst.research_sources = []
        out = await skill.deep_research(query="topic", breadth=2, depth=3)

    assert out["learnings"] == []
    assert out["context"] == []
    # No recursion into deeper layers with empty goals
    assert MockR.call_count == 2  # one per top-level query only
