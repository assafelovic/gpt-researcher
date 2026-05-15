from types import SimpleNamespace

import pytest

import gpt_researcher.skills.deep_research as deep_research_module
from gpt_researcher.skills.deep_research import (
    DeepResearchSkill,
    parse_follow_up_questions_response,
    parse_research_results_response,
    parse_search_queries_response,
)


def make_skill() -> DeepResearchSkill:
    cfg = SimpleNamespace(
        strategic_llm_provider="anthropic",
        strategic_llm_model="claude-haiku-4-5",
        reasoning_effort="medium",
        deep_research_breadth=3,
        deep_research_depth=2,
        deep_research_concurrency=2,
        config_path=None,
    )
    researcher = SimpleNamespace(
        cfg=cfg,
        websocket=None,
        tone=None,
        headers={},
        visited_urls=set(),
        retrievers=[SimpleNamespace()],
        research_sources=[],
        mcp_configs=None,
        mcp_strategy=None,
    )
    return DeepResearchSkill(researcher)


def stub_search_results(monkeypatch):
    async def fake_get_search_results(*args, **kwargs):
        return []

    monkeypatch.setattr(deep_research_module, "get_search_results", fake_get_search_results)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (
            '[{"query":"q1","researchGoal":"g1"},{"query":"q2","researchGoal":"g2"}]',
            [
                {"query": "q1", "researchGoal": "g1"},
                {"query": "q2", "researchGoal": "g2"},
            ],
        ),
        (
            'Sure — here is the JSON.\n```json\n[{"query":"q1","researchGoal":"g1"}]\n```',
            [{"query": "q1", "researchGoal": "g1"}],
        ),
        (
            "1. Query: q1\n   Goal: g1\n2. Query: q2\n   Goal: g2",
            [
                {"query": "q1", "researchGoal": "g1"},
                {"query": "q2", "researchGoal": "g2"},
            ],
        ),
        (
            "- Query: q1\n- Goal: g1\n- Query: q2\n- Goal: g2",
            [
                {"query": "q1", "researchGoal": "g1"},
                {"query": "q2", "researchGoal": "g2"},
            ],
        ),
        (
            "Query: q1\nGoal: g1\nQuery: q2\nGoal: g2",
            [
                {"query": "q1", "researchGoal": "g1"},
                {"query": "q2", "researchGoal": "g2"},
            ],
        ),
    ],
)
async def test_generate_search_queries_parses_supported_formats(monkeypatch, response, expected):
    skill = make_skill()

    async def fake_create_chat_completion(**kwargs):
        return response

    monkeypatch.setattr(deep_research_module, "create_chat_completion", fake_create_chat_completion)

    assert await skill.generate_search_queries("topic", num_queries=3) == expected


@pytest.mark.asyncio
async def test_generate_search_queries_prompt_requires_json(monkeypatch):
    skill = make_skill()
    captured = {}

    async def fake_create_chat_completion(**kwargs):
        captured["messages"] = kwargs["messages"]
        return "[]"

    monkeypatch.setattr(deep_research_module, "create_chat_completion", fake_create_chat_completion)

    await skill.generate_search_queries("topic", num_queries=2)

    system_prompt = captured["messages"][0]["content"]
    user_prompt = captured["messages"][1]["content"]
    assert "Return valid JSON only" in system_prompt
    assert "Return ONLY a JSON array of objects" in user_prompt


def test_parse_search_queries_response_repairs_trailing_comma():
    response = '[{"query": "test query", "researchGoal": "test goal",}]'

    result = parse_search_queries_response(response, num_queries=3)

    assert result
    assert result[0]["query"] == "test query"
    assert result[0]["researchGoal"] == "test goal"


def test_parse_search_queries_response_accepts_uppercase_json_fence():
    response = '```JSON\n[{"query": "x", "researchGoal": "y"}]\n```'

    result = parse_search_queries_response(response, num_queries=3)

    assert result
    assert result[0]["query"] == "x"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ('{"questions":["What changed in 2025?","What should we compare?"]}', ["What changed in 2025?", "What should we compare?"]),
        ('Intro\n```json\n{"questions":["What changed in 2025?"]}\n```', ["What changed in 2025?"]),
        ("1. Question: What changed in 2025?\n2. Question: What should we compare?", ["What changed in 2025?", "What should we compare?"]),
        ("- What changed in 2025?\n- What should we compare?", ["What changed in 2025?", "What should we compare?"]),
    ],
)
async def test_generate_research_plan_parses_supported_formats(monkeypatch, response, expected):
    skill = make_skill()
    stub_search_results(monkeypatch)

    async def fake_create_chat_completion(**kwargs):
        return response

    monkeypatch.setattr(deep_research_module, "create_chat_completion", fake_create_chat_completion)

    assert await skill.generate_research_plan("topic", num_questions=3) == expected


@pytest.mark.asyncio
async def test_generate_research_plan_prompt_requires_json(monkeypatch):
    skill = make_skill()
    captured = {}
    stub_search_results(monkeypatch)

    async def fake_create_chat_completion(**kwargs):
        captured["messages"] = kwargs["messages"]
        return '{"questions":[]}'

    monkeypatch.setattr(deep_research_module, "create_chat_completion", fake_create_chat_completion)

    await skill.generate_research_plan("topic", num_questions=2)

    system_prompt = captured["messages"][0]["content"]
    user_prompt = captured["messages"][1]["content"]
    assert "Return valid JSON only" in system_prompt
    assert '{"questions": ["<question 1>", "<question 2>"]}' in user_prompt


def test_parse_follow_up_questions_response_repairs_missing_quote():
    response = '{"questions": ["What is X", "Why is Y?]}'

    result = parse_follow_up_questions_response(response, num_questions=3)

    assert result
    assert result[0] == "What is X"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (
            '{"learnings":[{"insight":"Insight 1","sourceUrl":"https://a.test"},{"insight":"Insight 2","sourceUrl":""}],"followUpQuestions":["What next?","Why now?"]}',
            {
                "learnings": ["Insight 1", "Insight 2"],
                "followUpQuestions": ["What next?", "Why now?"],
                "citations": {"Insight 1": "https://a.test"},
            },
        ),
        (
            'Here is the JSON:\n```json\n{"learnings":[{"insight":"Insight 1","sourceUrl":"https://a.test"}],"followUpQuestions":["What next?"]}\n```',
            {
                "learnings": ["Insight 1"],
                "followUpQuestions": ["What next?"],
                "citations": {"Insight 1": "https://a.test"},
            },
        ),
        (
            "1. Learning [https://a.test]: Insight 1\n2. Learning [https://b.test]: Insight 2\n3. Question: What next?",
            {
                "learnings": ["Insight 1", "Insight 2"],
                "followUpQuestions": ["What next?"],
                "citations": {
                    "Insight 1": "https://a.test",
                    "Insight 2": "https://b.test",
                },
            },
        ),
        (
            "- Learning [https://a.test]: Insight 1\n- Learning: Insight 2 https://b.test\n- What next?",
            {
                "learnings": ["Insight 1", "Insight 2"],
                "followUpQuestions": ["What next?"],
                "citations": {
                    "Insight 1": "https://a.test",
                    "Insight 2": "https://b.test",
                },
            },
        ),
        (
            "Learning [https://a.test]: Insight 1\nQuestion: What next?",
            {
                "learnings": ["Insight 1"],
                "followUpQuestions": ["What next?"],
                "citations": {"Insight 1": "https://a.test"},
            },
        ),
    ],
)
async def test_process_research_results_parses_supported_formats(monkeypatch, response, expected):
    skill = make_skill()

    async def fake_create_chat_completion(**kwargs):
        return response

    monkeypatch.setattr(deep_research_module, "create_chat_completion", fake_create_chat_completion)

    assert await skill.process_research_results("topic", "context", num_learnings=3) == expected


@pytest.mark.asyncio
async def test_process_research_results_prompt_requires_json(monkeypatch):
    skill = make_skill()
    captured = {}

    async def fake_create_chat_completion(**kwargs):
        captured["messages"] = kwargs["messages"]
        return '{"learnings":[],"followUpQuestions":[]}'

    monkeypatch.setattr(deep_research_module, "create_chat_completion", fake_create_chat_completion)

    await skill.process_research_results("topic", "context", num_learnings=2)

    system_prompt = captured["messages"][0]["content"]
    user_prompt = captured["messages"][1]["content"]
    assert "Return valid JSON only" in system_prompt
    assert '"learnings": [{"insight": "<insight>", "sourceUrl": "<url or empty string>"}]' in user_prompt


def test_parse_responses_return_empty_values_for_blank_input():
    expected_research_results = {
        "learnings": [],
        "followUpQuestions": [],
        "citations": {},
    }

    for response in ("", "   \n  \t  "):
        assert parse_search_queries_response(response, num_queries=3) == []
        assert parse_follow_up_questions_response(response, num_questions=3) == []
        assert parse_research_results_response(response, num_learnings=3) == expected_research_results


def test_parse_research_results_response_preserves_full_json_url():
    response = (
        '{"learnings": [{"insight": "fact",'
        ' "sourceUrl": "https://example.com/path?x=1&y=2"}],'
        ' "followUpQuestions": []}'
    )

    result = parse_research_results_response(response, num_learnings=3)

    assert result["citations"]["fact"] == "https://example.com/path?x=1&y=2"


def test_parse_research_results_response_extracts_inline_legacy_url():
    response = "Learning: stuff happened at https://example.com/api/v1?key=value"

    result = parse_research_results_response(response, num_learnings=3)

    assert result["learnings"] == ["stuff happened at"]
    assert result["citations"]["stuff happened at"] == "https://example.com/api/v1?key=value"
