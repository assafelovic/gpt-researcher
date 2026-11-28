"""Unit tests for SemanticScholarSearch max_results guards and bounding."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from unittest.mock import MagicMock, patch

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PATH = (
    _ROOT / "gpt_researcher" / "retrievers" / "semantic_scholar" / "semantic_scholar.py"
)

_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.retrievers.semantic_scholar.semantic_scholar_under_test",
    _PATH,
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[
    "gpt_researcher.retrievers.semantic_scholar.semantic_scholar_under_test"
] = _mod
_spec.loader.exec_module(_mod)

SemanticScholarSearch = _mod.SemanticScholarSearch


def _mock_response(payload, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


def test_non_positive_max_results_returns_empty_without_request():
    searcher = SemanticScholarSearch("quantum computing")
    with patch("requests.get") as mock_get:
        assert searcher.search(max_results=0) == []
        assert searcher.search(max_results=-1) == []
        assert searcher.search(max_results=-10) == []
        mock_get.assert_not_called()


def test_max_results_limits_api_parameter_up_to_100():
    searcher = SemanticScholarSearch("deep learning")
    with patch("requests.get", return_value=_mock_response({"data": []})) as mock_get:
        searcher.search(max_results=5)
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["limit"] == 5

    with patch("requests.get", return_value=_mock_response({"data": []})) as mock_get:
        searcher.search(max_results=150)
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        # Semantic Scholar caps limit at 100
        assert kwargs["params"]["limit"] == 100


def test_bounds_results_to_max_results():
    searcher = SemanticScholarSearch("transformers")
    payload = {
        "data": [
            {
                "title": f"Paper {i}",
                "isOpenAccess": True,
                "openAccessPdf": {"url": f"https://example.com/p{i}.pdf"},
                "abstract": f"Abstract {i}",
            }
            for i in range(10)
        ]
    }
    with patch("requests.get", return_value=_mock_response(payload)):
        results = searcher.search(max_results=3)
        assert len(results) == 3
        assert results[0]["title"] == "Paper 0"
        assert results[0]["href"] == "https://example.com/p0.pdf"
        assert results[2]["title"] == "Paper 2"
        assert results[2]["href"] == "https://example.com/p2.pdf"


def test_query_domains_stored():
    searcher_domains = SemanticScholarSearch(
        "machine learning", query_domains=["arxiv.org"]
    )
    assert searcher_domains.query_domains == ["arxiv.org"]

    searcher_none = SemanticScholarSearch("machine learning")
    assert searcher_none.query_domains is None

    searcher_empty = SemanticScholarSearch("machine learning", query_domains=[])
    assert searcher_empty.query_domains is None
