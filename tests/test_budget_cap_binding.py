import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from gpt_researcher.exceptions import BudgetExceededError
from gpt_researcher.skills.deep_research import DeepResearchSkill
from gpt_researcher.utils.enum import Tone
from gpt_researcher.agent import GPTResearcher


class _BudgetedNestedResearcher:
    add_costs = GPTResearcher.add_costs
    get_costs = GPTResearcher.get_costs

    def __init__(self, *args, budget_state=None, **kwargs):
        if budget_state is None:
            raise AssertionError("Nested researcher must share the parent budget_state")
        self.budget_state = budget_state
        self.research_costs = 0.0
        self.step_costs = {}
        self._current_step = "research"
        self.log_handler = None
        self.visited_urls = set()
        self.research_sources = []

    async def conduct_research(self):
        self.add_costs(0.03)
        self.add_costs(0.03)
        return "context"


class TestBudgetCapBinding(unittest.TestCase):
    def test_deep_research_nested_researchers_share_budget_state(self):
        parent_researcher = SimpleNamespace(
            cfg=SimpleNamespace(
                deep_research_breadth=1,
                deep_research_depth=1,
                deep_research_concurrency=1,
                config_path=None,
                strategic_llm_provider="anthropic",
                strategic_llm_model="claude-sonnet-4-6",
                reasoning_effort="medium",
            ),
            websocket=None,
            tone=Tone.Objective,
            headers={},
            visited_urls=set(),
            mcp_configs=None,
            mcp_strategy=None,
            budget_state={"max_cost_usd": 0.05, "total_cost_usd": 0.0},
            research_costs=0.0,
            add_costs=AsyncMock(),
        )
        skill = DeepResearchSkill(parent_researcher)
        skill.generate_search_queries = AsyncMock(
            return_value=[{"query": "sub-query", "researchGoal": "goal"}]
        )

        with patch("gpt_researcher.GPTResearcher", _BudgetedNestedResearcher):
            with self.assertRaises(BudgetExceededError):
                asyncio.run(skill.deep_research("root query", breadth=1, depth=1))


if __name__ == "__main__":
    unittest.main()
