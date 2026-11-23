"""``add_costs`` must deliver ``cost_update`` events to a custom log handler.

``add_costs`` is synchronous but ``_log_event`` is a coroutine, so calling it
without scheduling dropped every event with "coroutine was never awaited".
"""

import asyncio

from gpt_researcher import GPTResearcher


class _RecordingHandler:
    def __init__(self):
        self.steps = []

    async def on_research_step(self, step, details):
        self.steps.append((step, details))


def _researcher(handler):
    researcher = GPTResearcher.__new__(GPTResearcher)
    researcher.research_costs = 0.0
    researcher.step_costs = {}
    researcher._current_step = "research"
    researcher.log_handler = handler
    return researcher


async def test_cost_update_reaches_the_log_handler():
    handler = _RecordingHandler()
    researcher = _researcher(handler)

    researcher.add_costs(0.01)
    researcher.add_costs(0.02)
    await asyncio.sleep(0)

    assert [step for step, _ in handler.steps] == ["cost_update", "cost_update"]
    assert handler.steps[-1][1]["total_cost"] == researcher.get_costs()
    assert handler.steps[-1][1]["step_name"] == "research"


def test_add_costs_without_a_running_loop_still_accumulates():
    researcher = _researcher(_RecordingHandler())

    researcher.add_costs(0.01)

    assert researcher.get_costs() == 0.01
    assert researcher.get_step_costs() == {"research": 0.01}
