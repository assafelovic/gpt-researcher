"""``MCPToolSelector.select_relevant_tools`` must honour its ``max_tools`` cap.

The LLM picks tools by index from the list it was shown. Its answer is a
suggestion, not a constraint: models routinely return more entries than asked
for (and can repeat an index), so the selection path has to apply the same
``max_tools`` limit the pattern-matching fallback already applies with
``scored_tools[:max_tools]``.

Without that limit every extra entry is bound to the research LLM
(``bind_tools(selected_tools)``) even though the caller asked for at most
``max_tools`` tools -- bigger prompts, higher cost, and duplicates of a tool that
is meant to be used once.
"""

import json
from types import SimpleNamespace

import pytest

from gpt_researcher.mcp.tool_selector import MCPToolSelector


class FakeTool:
    def __init__(self, name):
        self.name = name
        self.description = f"{name} description"


TOOLS = [FakeTool(f"tool_{i}") for i in range(5)]


def make_selector(selection):
    selector = MCPToolSelector(SimpleNamespace())

    async def fake_llm(prompt):
        return json.dumps(selection)

    selector._call_llm_for_tool_selection = fake_llm
    return selector


@pytest.mark.asyncio
async def test_llm_selection_is_capped_at_max_tools():
    selector = make_selector({"selected_tools": [{"index": i} for i in range(5)]})

    picked = await selector.select_relevant_tools("query", TOOLS, max_tools=2)

    assert [tool.name for tool in picked] == ["tool_0", "tool_1"]


@pytest.mark.asyncio
async def test_llm_selection_drops_repeated_indexes():
    selector = make_selector({"selected_tools": [{"index": 0}, {"index": 0}, {"index": 1}]})

    picked = await selector.select_relevant_tools("query", TOOLS, max_tools=3)

    assert [tool.name for tool in picked] == ["tool_0", "tool_1"]


@pytest.mark.asyncio
async def test_selection_below_the_cap_is_unchanged():
    selector = make_selector({"selected_tools": [{"index": 3}, {"index": 1}]})

    picked = await selector.select_relevant_tools("query", TOOLS, max_tools=3)

    assert [tool.name for tool in picked] == ["tool_3", "tool_1"]
