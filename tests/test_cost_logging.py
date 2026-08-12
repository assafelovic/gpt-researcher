import asyncio
import builtins
import importlib
import typing
import unittest
from unittest.mock import AsyncMock, patch


def _load_researcher_class():
    with (
        patch.object(builtins, "Any", typing.Any, create=True),
        patch.object(builtins, "List", typing.List, create=True),
    ):
        return importlib.import_module("gpt_researcher.agent").GPTResearcher


GPTResearcher = _load_researcher_class()


class CostLoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_add_costs_schedules_cost_update_log(self):
        researcher = GPTResearcher.__new__(GPTResearcher)
        researcher.research_costs = 0.0
        researcher.step_costs = {}
        researcher._background_tasks = set()
        researcher._current_step = "research"
        researcher.log_handler = AsyncMock()

        researcher.add_costs(0.25)
        await asyncio.sleep(0)

        self.assertEqual(researcher.research_costs, 0.25)
        self.assertEqual(researcher.step_costs, {"research": 0.25})
        researcher.log_handler.on_research_step.assert_awaited_once_with(
            "cost_update",
            {
                "cost": 0.25,
                "total_cost": 0.25,
                "step_name": "research",
            },
        )


class SynchronousCostLoggingTests(unittest.TestCase):
    def test_add_costs_without_running_loop_still_accumulates(self):
        researcher = GPTResearcher.__new__(GPTResearcher)
        researcher.research_costs = 0.0
        researcher.step_costs = {}
        researcher._background_tasks = set()
        researcher._current_step = "research"
        researcher.log_handler = AsyncMock()

        researcher.add_costs(0.25)

        self.assertEqual(researcher.research_costs, 0.25)
        self.assertEqual(researcher.step_costs, {"research": 0.25})
        researcher.log_handler.on_research_step.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
