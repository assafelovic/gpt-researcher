from gpt_researcher.actions.query_processing import (
    _complete_sub_queries,
    _extract_focus_terms,
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


def test_complete_sub_queries_falls_back_to_anchored_queries():
    query = "What are the practical tradeoffs between FastAPI and Flask for async Python APIs?"
    response = [
        "django vs flask tutorial",
        "spring boot rest api guide",
    ]

    result = _complete_sub_queries(response, query, "", 3)

    assert result[0] == query
    assert len(result) == 3
    assert all("django" not in candidate.lower() for candidate in result)
    assert all("spring boot" not in candidate.lower() for candidate in result)


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
