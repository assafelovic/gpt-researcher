"""Tests for TavilySearch query_domains filtering, result bounding, and non-positive max_results guards."""

import importlib.util
import pathlib
from unittest.mock import patch

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "tavily"
    / "tavily_search.py"
)
_spec = importlib.util.spec_from_file_location("_tavily_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
TavilySearch = _mod.TavilySearch


def test_tavily_non_positive_max_results_returns_empty_without_request():
    searcher = TavilySearch("test query", headers={"tavily_api_key": "dummy"})
    with patch.object(searcher, "_search") as mock_search:
        assert searcher.search(max_results=0) == []
        assert searcher.search(max_results=-1) == []
        mock_search.assert_not_called()


def test_tavily_query_domains_passed_to_search():
    searcher = TavilySearch(
        "quantum computing",
        query_domains=["arxiv.org", "nature.com"],
        headers={"tavily_api_key": "dummy"},
    )
    with patch.object(searcher, "_search", return_value={"results": []}) as mock_search:
        searcher.search(max_results=5)
        mock_search.assert_called_once()
        _, kwargs = mock_search.call_args
        assert kwargs["include_domains"] == ["arxiv.org", "nature.com"]
        assert kwargs["max_results"] == 5


def test_tavily_query_domains_filters_empty_and_whitespace():
    searcher = TavilySearch(
        "machine learning",
        query_domains=["", "   ", None, "  example.com  ", 123, "openai.com"],
        headers={"tavily_api_key": "dummy"},
    )
    with patch.object(searcher, "_search", return_value={"results": []}) as mock_search:
        searcher.search(max_results=5)
        mock_search.assert_called_once()
        _, kwargs = mock_search.call_args
        assert kwargs["include_domains"] == ["example.com", "openai.com"]


def test_tavily_query_domains_all_empty_passes_none():
    searcher = TavilySearch(
        "machine learning",
        query_domains=["", "   ", None],
        headers={"tavily_api_key": "dummy"},
    )
    with patch.object(searcher, "_search", return_value={"results": []}) as mock_search:
        searcher.search(max_results=5)
        mock_search.assert_called_once()
        _, kwargs = mock_search.call_args
        assert kwargs["include_domains"] is None


def test_tavily_site_operator_combined_and_cleaned():
    searcher = TavilySearch(
        "site:arxiv.org/abs/1234 deep learning",
        query_domains=["nature.com", "  ", ""],
        headers={"tavily_api_key": "dummy"},
    )
    with patch.object(searcher, "_search", return_value={"results": []}) as mock_search:
        searcher.search(max_results=5)
        mock_search.assert_called_once()
        args, kwargs = mock_search.call_args
        assert args[0] == "deep learning"
        assert kwargs["include_domains"] == ["arxiv.org", "nature.com"]


def test_tavily_bounds_results_to_max_results():
    searcher = TavilySearch("test", headers={"tavily_api_key": "dummy"})
    payload = {
        "results": [
            {"url": f"https://example.com/{i}", "content": f"Content {i}"}
            for i in range(10)
        ]
    }
    with patch.object(searcher, "_search", return_value=payload):
        results = searcher.search(max_results=3)
        assert len(results) == 3
        assert results[0]["href"] == "https://example.com/0"
        assert results[2]["href"] == "https://example.com/2"
