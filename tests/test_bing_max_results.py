"""Unit tests for BingSearch max_results guards, result bounding, and domain cleaning."""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
from unittest.mock import patch

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_BING_PATH = _ROOT / "gpt_researcher" / "retrievers" / "bing" / "bing.py"

_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.retrievers.bing.bing_under_test",
    _BING_PATH,
)
_bing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bing)
BingSearch = _bing.BingSearch


class _FakeResp:
    def __init__(self, payload):
        self.text = json.dumps(payload)

    def raise_for_status(self):
        return None


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_non_positive_max_results_returns_empty_without_request():
    searcher = BingSearch("artificial intelligence")
    with patch.object(_bing.requests, "get") as mock_get:
        assert searcher.search(max_results=0) == []
        assert searcher.search(max_results=-1) == []
        assert searcher.search(max_results=-10) == []
        mock_get.assert_not_called()


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bounds_results_to_max_results():
    searcher = BingSearch("machine learning")
    payload = {
        "webPages": {
            "value": [
                {
                    "name": f"Result {i}",
                    "url": f"https://example.com/page{i}",
                    "snippet": f"Snippet {i}",
                }
                for i in range(5)
            ]
        }
    }
    with patch.object(_bing.requests, "get", return_value=_FakeResp(payload)):
        results = searcher.search(max_results=2)
        assert len(results) == 2
        assert results[0]["title"] == "Result 0"
        assert results[1]["title"] == "Result 1"


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bing_query_domains_filters_whitespace_and_empty():
    searcher = BingSearch(
        "python", query_domains=["docs.python.org", "   ", "", "github.com"]
    )
    payload = {"webPages": {"value": []}}
    with patch.object(
        _bing.requests, "get", return_value=_FakeResp(payload)
    ) as mock_get:
        searcher.search(max_results=5)

    assert mock_get.called
    sent_params = mock_get.call_args.kwargs["params"]
    assert sent_params["q"] == "(site:docs.python.org OR site:github.com) python"


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_query_domains_stored():
    searcher_domains = BingSearch("test", query_domains=["example.com"])
    assert searcher_domains.query_domains == ["example.com"]

    searcher_none = BingSearch("test")
    assert searcher_none.query_domains is None

    searcher_empty = BingSearch("test", query_domains=[])
    assert searcher_empty.query_domains is None
