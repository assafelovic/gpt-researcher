"""Deep research keeps its cited learnings when the scraped context fills the word limit."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from gpt_researcher.skills.deep_research import MAX_CONTEXT_WORDS, DeepResearchSkill


@pytest.mark.asyncio
async def test_learnings_survive_full_context():
    researcher = SimpleNamespace(
        cfg=SimpleNamespace(
            deep_research_breadth=2,
            deep_research_depth=1,
            deep_research_concurrency=2,
            strategic_llm_provider="openai",
            strategic_llm_model="gpt",
            reasoning_effort=None,
            config_path=None,
        ),
        query="topic",
        websocket=None,
        tone=None,
        headers={},
        visited_urls=set(),
        mcp_configs=None,
        mcp_strategy=None,
        log_handler=None,
        get_costs=lambda: 0.0,
    )
    skill = DeepResearchSkill(researcher)
    skill.generate_research_plan = AsyncMock(return_value=[])
    skill.deep_research = AsyncMock(return_value={
        "learnings": ["Acme raised $40M in 2025"],
        "citations": {"Acme raised $40M in 2025": "https://news.test/acme"},
        "context": ["scraped " * (MAX_CONTEXT_WORDS // 2)] * 2,
        "visited_urls": [],
        "sources": [],
    })

    context = await skill.run()

    assert "Acme raised $40M in 2025 [Source: https://news.test/acme]" in context
