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


@pytest.mark.asyncio
@pytest.mark.parametrize("second_result", ["no_queries", "failed_queries", "no_sources", "new_sources"])
async def test_repeat_run_publishes_current_sources(monkeypatch, second_result):
    from gpt_researcher import GPTResearcher

    parent = SimpleNamespace(
        cfg=SimpleNamespace(
            deep_research_breadth=1,
            deep_research_depth=1,
            deep_research_concurrency=1,
            config_path=None,
        ),
        websocket=None, tone=None, headers={}, visited_urls=set(),
        mcp_configs=None, mcp_strategy=None, query="topic",
        get_costs=lambda: 0, add_costs=lambda _cost: None,
        log_handler=None, research_sources=[],
    )
    skill = DeepResearchSkill(parent)
    stage = "first"

    async def plan(query):
        return []

    async def queries(query, num_queries=3):
        if stage == "second" and second_result == "no_queries":
            return []
        return [{"query": stage, "researchGoal": "local test"}]

    async def extract(query, context):
        return {"learnings": [], "followUpQuestions": [], "citations": {}}

    class LocalResearcher:
        def __init__(self, **kwargs):
            self.visited_urls = {"https://example.invalid/" + stage}
            self.research_sources = [{"url": "https://example.invalid/" + stage}]
            if stage == "second" and second_result == "no_sources":
                self.research_sources = []

        def get_costs(self):
            return 0.0

        async def conduct_research(self):
            if stage == "second" and second_result == "failed_queries":
                raise RuntimeError("synthetic local failure")
            return stage + " context"

    monkeypatch.setattr(skill, "generate_research_plan", plan)
    monkeypatch.setattr(skill, "generate_search_queries", queries)
    monkeypatch.setattr(skill, "process_research_results", extract)
    monkeypatch.setattr("gpt_researcher.GPTResearcher", LocalResearcher)

    assert await skill.run() == "first context"
    assert GPTResearcher.get_research_sources(parent) == [{"url": "https://example.invalid/first"}]
    prior_tracking = list(skill.research_sources)

    stage = "second"
    context = await skill.run()
    expected_context = "" if second_result in ("no_queries", "failed_queries") else "second context"
    expected_sources = [{"url": "https://example.invalid/second"}] if second_result == "new_sources" else []
    assert context == expected_context
    assert GPTResearcher.get_research_context(parent) == expected_context
    assert GPTResearcher.get_research_sources(parent) == expected_sources
    # Public publication must not erase the skill's separate cumulative history.
    if second_result != "new_sources":
        assert skill.research_sources == prior_tracking
