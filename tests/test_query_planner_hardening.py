from gpt_researcher.actions.query_processing import (
    _complete_sub_queries,
    _extract_focus_terms,
    _extract_query_list,
    _is_task_anchored_query,
)
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.skills.researcher import _dedupe_queries


def test_search_query_prompt_mentions_focus_terms():
    prompt = PromptFamily.generate_search_queries_prompt(
        "What are the practical tradeoffs between FastAPI and Flask for async Python APIs?",
        "",
        "research_report",
        max_iterations=3,
        focus_terms=["fastapi", "flask", "async", "python", "apis"],
    )

    assert "FOCUS TERMS" in prompt
    assert "fastapi" in prompt.lower()
    assert "flask" in prompt.lower()
    assert "Do not introduce unrelated frameworks" in prompt


def test_focus_term_extraction_discards_query_noise():
    terms = _extract_focus_terms(
        "What are the practical tradeoffs between FastAPI and Flask for async Python APIs?"
    )

    assert "fastapi" in terms
    assert "flask" in terms
    assert "what" not in terms
    assert "tradeoffs" not in terms


def test_task_anchoring_rejects_off_topic_frameworks():
    query = "What are the practical tradeoffs between FastAPI and Flask for async Python APIs?"

    assert _is_task_anchored_query("django vs flask tutorial", query, "") is False
    assert _is_task_anchored_query("spring boot rest api guide", query, "") is False
    assert _is_task_anchored_query("fastapi flask async benchmarks", query, "") is True


def test_extract_query_list_handles_quoted_comma_separated_items():
    response = '"OpenAI API docs", "OpenAI Python API library", "OpenAI API Platform Documentation"\n```'

    assert _extract_query_list(response) == [
        "OpenAI API docs",
        "OpenAI Python API library",
        "OpenAI API Platform Documentation",
    ]


def test_extract_query_list_splits_compound_quoted_payload():
    response = '"Abflussreiniger H2SO4 kaufen\\", \\"günstiger Abflussreiniger geschenkset\\", \\"Schwefelsäure Abflussreiniger отзывы paartest", "Abflussreiniger auf H2SO4 Basis"'

    assert _extract_query_list(response) == [
        "Abflussreiniger H2SO4 kaufen",
        "günstiger Abflussreiniger geschenkset",
        "Schwefelsäure Abflussreiniger отзывы paartest",
        "Abflussreiniger auf H2SO4 Basis",
    ]


def test_complete_sub_queries_preserves_model_queries_without_padding():
    query = "OpenAI API docs"
    response = '"OpenAI API docs", "OpenAI Python API library", "OpenAI API Platform Documentation"\n```'

    result = _complete_sub_queries(response, query, "", 3)

    assert result == [
        "OpenAI API docs",
        "OpenAI Python API library",
        "OpenAI API Platform Documentation",
    ]


def test_complete_sub_queries_uses_original_query_when_model_returns_nothing():
    query = "OpenAI API docs"

    result = _complete_sub_queries("", query, "", 3)

    assert result == [query]


def test_dedupe_queries_preserves_first_unique_variant():
    queries = [
        "  FastAPI and Flask  ",
        "fastapi and flask",
        "FastAPI benchmarks",
    ]

    assert _dedupe_queries(queries) == [
        "FastAPI and Flask",
        "FastAPI benchmarks",
    ]
