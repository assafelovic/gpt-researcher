"""MCP tool selector should recover fenced LLM JSON via json_repair."""

from types import SimpleNamespace

import pytest

from gpt_researcher.mcp.tool_selector import MCPToolSelector


class _Tool:
    def __init__(self, name, description="d"):
        self.name = name
        self.description = description


@pytest.mark.asyncio
async def test_select_recovers_fenced_json(monkeypatch):
    selector = MCPToolSelector(cfg=SimpleNamespace())
    tools = [_Tool("a"), _Tool("b"), _Tool("c")]

    async def fake_llm(prompt):
        return (
            'Pick these:\n```json\n'
            '{"selected_tools":[{"index":1,"name":"b","reason":"yes","relevance_score":9}],'
            '"selection_reasoning":"best"}\n```'
        )

    monkeypatch.setattr(selector, "_call_llm_for_tool_selection", fake_llm)
    # avoid prompt import path churn if select builds prompt first
    monkeypatch.setattr(
        "gpt_researcher.prompts.PromptFamily.generate_mcp_tool_selection_prompt",
        staticmethod(lambda *a, **k: "prompt"),
        raising=False,
    )
    # patch where imported inside method
    import gpt_researcher.mcp.tool_selector as mod

    class PF:
        @staticmethod
        def generate_mcp_tool_selection_prompt(*a, **k):
            return "prompt"

    monkeypatch.setattr(mod, "PromptFamily", PF, raising=False)

    # The method does: from ..prompts import PromptFamily inside try path
    import gpt_researcher.prompts as prompts_mod

    monkeypatch.setattr(
        prompts_mod.PromptFamily,
        "generate_mcp_tool_selection_prompt",
        staticmethod(lambda *a, **k: "prompt"),
    )

    selected = await selector.select_relevant_tools("q", tools, max_tools=2)
    assert [t.name for t in selected] == ["b"]


@pytest.mark.asyncio
async def test_select_skips_non_dict_tool_rows(monkeypatch):
    selector = MCPToolSelector(cfg=SimpleNamespace())
    tools = [_Tool("a"), _Tool("b")]

    async def fake_llm(prompt):
        return '{"selected_tools":[null, {"index":0,"name":"a","reason":"r","relevance_score":1}],"selection_reasoning":"x"}'

    monkeypatch.setattr(selector, "_call_llm_for_tool_selection", fake_llm)
    import gpt_researcher.prompts as prompts_mod

    monkeypatch.setattr(
        prompts_mod.PromptFamily,
        "generate_mcp_tool_selection_prompt",
        staticmethod(lambda *a, **k: "prompt"),
    )

    selected = await selector.select_relevant_tools("q", tools, max_tools=2)
    assert [t.name for t in selected] == ["a"]
