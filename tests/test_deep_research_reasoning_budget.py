from types import SimpleNamespace

import pytest

import gpt_researcher.skills.deep_research as deep_research_module
from gpt_researcher.skills.deep_research import DeepResearchSkill


def make_skill(*, strategic_token_limit=8000):
    cfg = SimpleNamespace(
        strategic_llm_provider="openai",
        strategic_llm_model="gpt-5.4",
        strategic_token_limit=strategic_token_limit,
        reasoning_effort="medium",
        deep_research_breadth=3,
        deep_research_depth=2,
        deep_research_concurrency=2,
        config_path=None,
        llm_kwargs={},
    )
    researcher = SimpleNamespace(
        cfg=cfg,
        websocket=None,
        tone=None,
        headers={},
        visited_urls=set(),
        retrievers=[],
        research_sources=[],
        add_costs=lambda _cost: None,
    )
    return DeepResearchSkill(researcher)


@pytest.mark.asyncio
async def test_process_research_results_uses_configured_strategic_token_limit(
    monkeypatch,
):
    skill = make_skill(strategic_token_limit=8000)
    captured = {}

    async def fake_create_chat_completion(**kwargs):
        captured.update(kwargs)
        return '{"learnings": [], "followUpQuestions": []}'

    monkeypatch.setattr(
        deep_research_module,
        "create_chat_completion",
        fake_create_chat_completion,
    )

    await skill.process_research_results("topic", "context")

    assert captured["max_tokens"] == 8000


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("generate_search_queries", ("topic",)),
        ("generate_research_plan", ("topic",)),
        ("process_research_results", ("topic", "context")),
    ],
)
async def test_deep_research_llm_calls_report_cost_to_parent_researcher(
    monkeypatch, method_name, args
):
    skill = make_skill()
    captured = {}

    async def fake_create_chat_completion(**kwargs):
        captured.update(kwargs)
        return (
            '{"queries": [], "questions": [], "learnings": [], '
            '"followUpQuestions": []}'
        )

    monkeypatch.setattr(
        deep_research_module,
        "create_chat_completion",
        fake_create_chat_completion,
    )

    await getattr(skill, method_name)(*args)

    assert captured["cost_callback"] is skill.researcher.add_costs
