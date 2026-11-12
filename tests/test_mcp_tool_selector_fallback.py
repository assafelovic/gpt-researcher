"""Unit and regression tests for MCPToolSelector fallback and parameter robustness."""

from types import SimpleNamespace

import pytest

from gpt_researcher.mcp.tool_selector import MCPToolSelector


class DummyTool:
    def __init__(self, name, description=None):
        self.name = name
        self.description = description


@pytest.mark.asyncio
@pytest.mark.parametrize("max_tools", [0, -1, -5])
async def test_non_positive_max_tools_returns_empty(max_tools):
    selector = MCPToolSelector(cfg=SimpleNamespace())
    tools = [DummyTool("search_web", "Search the internet"), DummyTool("fetch_data", "Fetch data")]

    # Should return empty without calling LLM or failing in slice
    selected = await selector.select_relevant_tools("query", tools, max_tools=max_tools)
    assert selected == []


def test_fallback_non_positive_max_tools_returns_empty():
    selector = MCPToolSelector(cfg=SimpleNamespace())
    tools = [DummyTool("search_web", "Search the internet")]

    assert selector._fallback_tool_selection(tools, max_tools=0) == []
    assert selector._fallback_tool_selection(tools, max_tools=-1) == []


def test_fallback_handles_tool_with_none_name_and_description():
    selector = MCPToolSelector(cfg=SimpleNamespace())
    # Tool with None name and None description
    tools = [
        DummyTool(None, None),
        DummyTool("search_docs", "Read documentation"),
    ]

    # Must not raise AttributeError: 'NoneType' object has no attribute 'lower'
    selected = selector._fallback_tool_selection(tools, max_tools=2)
    assert len(selected) >= 1
    assert selected[0].name == "search_docs"


def test_fallback_selects_first_tools_when_no_pattern_matches():
    selector = MCPToolSelector(cfg=SimpleNamespace())
    # Tools whose names and descriptions do not contain the hardcoded keyword patterns
    tools = [
        DummyTool("summarize_text", "Produce concise executive synopsis"),
        DummyTool("mortgage_calc", "Compute amortization schedule"),
        DummyTool("weather_forecast", "Atmospheric humidity predictions"),
    ]

    selected = selector._fallback_tool_selection(tools, max_tools=2)
    assert len(selected) == 2
    assert [t.name for t in selected] == ["summarize_text", "mortgage_calc"]


def test_fallback_prioritizes_pattern_matches_over_non_matches():
    selector = MCPToolSelector(cfg=SimpleNamespace())
    tools = [
        DummyTool("weather_forecast", "Atmospheric humidity predictions"),
        DummyTool("search_database", "Query records in SQL"),
        DummyTool("mortgage_calc", "Compute amortization schedule"),
    ]

    selected = selector._fallback_tool_selection(tools, max_tools=1)
    assert len(selected) == 1
    assert selected[0].name == "search_database"


@pytest.mark.asyncio
async def test_select_tools_info_handles_none_name(monkeypatch):
    selector = MCPToolSelector(cfg=SimpleNamespace())
    tools = [DummyTool(None, None)]

    captured_prompt = {}

    def fake_generate_prompt(query, tools_info, max_tools):
        captured_prompt["tools_info"] = tools_info
        return "fake prompt"

    import gpt_researcher.prompts as prompts_mod
    monkeypatch.setattr(
        prompts_mod.PromptFamily,
        "generate_mcp_tool_selection_prompt",
        staticmethod(fake_generate_prompt),
    )

    async def fake_llm(prompt):
        return None  # Trigger fallback

    monkeypatch.setattr(selector, "_call_llm_for_tool_selection", fake_llm)

    selected = await selector.select_relevant_tools("test query", tools, max_tools=1)
    assert len(selected) == 1
    assert selected[0].name is None
    assert captured_prompt["tools_info"][0]["name"] == "tool_0"
    assert captured_prompt["tools_info"][0]["description"] == "No description available"
