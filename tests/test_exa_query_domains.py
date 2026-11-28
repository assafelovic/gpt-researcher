"""Tests for ExaSearch query_domains filtering, result bounding, and non-positive max_results guards."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Set up module namespace so relative imports work without full package initialization
if "gpt_researcher.retrievers.utils" not in sys.modules:
    _p_utils = _ROOT / "gpt_researcher" / "retrievers" / "utils.py"
    _spec_utils = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.utils", _p_utils
    )
    _mod_utils = importlib.util.module_from_spec(_spec_utils)
    sys.modules["gpt_researcher.retrievers.utils"] = _mod_utils
    _spec_utils.loader.exec_module(_mod_utils)

_p_exa = _ROOT / "gpt_researcher" / "retrievers" / "exa" / "exa.py"
_spec_exa = importlib.util.spec_from_file_location(
    "gpt_researcher.retrievers.exa.exa", _p_exa
)
_mod_exa = importlib.util.module_from_spec(_spec_exa)
sys.modules["gpt_researcher.retrievers.exa.exa"] = _mod_exa
_spec_exa.loader.exec_module(_mod_exa)

ExaSearch = _mod_exa.ExaSearch


def _searcher(query="test", query_domains=None):
    s = ExaSearch.__new__(ExaSearch)
    s.query = query
    s.query_domains = query_domains
    s.api_key = "dummy"
    s.client = MagicMock()
    return s


def test_exa_non_positive_max_results_returns_empty_without_request():
    s = _searcher("test query")
    assert s.search(max_results=0) == []
    assert s.search(max_results=-1) == []
    s.client.search.assert_not_called()


def test_exa_query_domains_passed_to_search():
    s = _searcher("quantum computing", query_domains=["arxiv.org", "nature.com"])
    s.client.search.return_value = SimpleNamespace(results=[])
    res = s.search(max_results=5)
    assert res == []
    s.client.search.assert_called_once()
    _, kwargs = s.client.search.call_args
    assert kwargs["include_domains"] == ["arxiv.org", "nature.com"]
    assert kwargs["num_results"] == 5


def test_exa_query_domains_filters_empty_and_whitespace():
    s = _searcher(
        "machine learning",
        query_domains=[
            "",
            "   ",
            None,
            "  example.com  ",
            123,
            "openai.com",
            "example.com",
        ],
    )
    s.client.search.return_value = SimpleNamespace(results=[])
    s.search(max_results=5)
    s.client.search.assert_called_once()
    _, kwargs = s.client.search.call_args
    assert kwargs["include_domains"] == ["example.com", "openai.com"]


def test_exa_query_domains_all_empty_passes_none():
    s = _searcher("machine learning", query_domains=["", "   ", None])
    s.client.search.return_value = SimpleNamespace(results=[])
    s.search(max_results=5)
    s.client.search.assert_called_once()
    _, kwargs = s.client.search.call_args
    assert kwargs["include_domains"] is None


def test_exa_bounds_results_to_max_results():
    s = _searcher("test")
    s.client.search.return_value = SimpleNamespace(
        results=[
            SimpleNamespace(
                url=f"https://example.com/{i}", text=f"Text {i}", summary=None
            )
            for i in range(10)
        ]
    )
    results = s.search(max_results=3)
    assert len(results) == 3
    assert results[0]["href"] == "https://example.com/0"
    assert results[2]["href"] == "https://example.com/2"
