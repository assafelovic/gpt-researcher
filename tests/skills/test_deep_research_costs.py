"""Deep research adds the costs of its own LLM calls and nested researchers to the parent."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import gpt_researcher.skills.deep_research as deep_research
from gpt_researcher.skills.deep_research import DeepResearchSkill


@pytest.mark.asyncio
async def test_costs_reach_the_parent(monkeypatch):
    costs = []
    researcher = SimpleNamespace(
        cfg=SimpleNamespace(
            deep_research_breadth=2,
            deep_research_depth=1,
            deep_research_concurrency=2,
            strategic_llm_provider="openai",
            strategic_llm_model="gpt",
            reasoning_effort=None,
            config_path=None,
            llm_kwargs={},
        ),
        websocket=None,
        tone=None,
        headers={},
        visited_urls=set(),
        mcp_configs=None,
        mcp_strategy=None,
        add_costs=costs.append,
    )
    skill = DeepResearchSkill(researcher)

    async def fake_completion(**kwargs):
        if kwargs.get("cost_callback"):
            kwargs["cost_callback"](0.01)
        if "search queries" in kwargs["messages"][1]["content"]:
            return '[{"query": "q1", "researchGoal": "g1"}, {"query": "q2", "researchGoal": "g2"}]'
        return '{"learnings": [{"insight": "x", "sourceUrl": ""}], "followUpQuestions": []}'

    monkeypatch.setattr(deep_research, "create_chat_completion", fake_completion)

    def nested_researcher(*args, **kwargs):
        nested = MagicMock()
        nested.visited_urls = set()
        nested.research_sources = []
        nested.conduct_research = AsyncMock(return_value="context")
        nested.get_costs.return_value = 1.0
        return nested

    with patch("gpt_researcher.GPTResearcher", side_effect=nested_researcher):
        await skill.deep_research(query="topic", breadth=2, depth=1)

    # two nested researchers, one query generation call and two learning extractions
    assert sum(costs) == pytest.approx(2.03)
