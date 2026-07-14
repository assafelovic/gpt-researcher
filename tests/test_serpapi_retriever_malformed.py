"""Regression tests for SerpApiSearch result normalization.

Without the fix, a response missing ``organic_results`` raises a KeyError, and
a single result missing ``title``/``link``/``snippet`` raises a KeyError that
aborts the whole ``search()`` call.
"""
import importlib.util
import os
import pathlib
from unittest.mock import patch

# Import the module directly to avoid importing the heavy gpt_researcher package
# (which pulls optional deps at import time).
_SERPAPI_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher" / "retrievers" / "serpapi" / "serpapi.py"
)
_spec = importlib.util.spec_from_file_location("_serpapi_under_test", _SERPAPI_PATH)
_serpapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_serpapi)
SerpApiSearch = _serpapi.SerpApiSearch


class _FakeResp:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload

    def json(self):
        return self._payload


@patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
def test_serpapi_skips_results_missing_keys():
    payload = {
        "organic_results": [
            {"title": "A", "link": "https://a.example", "snippet": "sa"},
            {"title": "B", "link": "https://b.example"},  # missing snippet
            {"link": "https://c.example"},  # missing title + snippet
            {"title": "D", "snippet": "sd"},  # missing link -> skipped
        ]
    }
    with patch.object(_serpapi.requests, "get", return_value=_FakeResp(payload)):
        results = SerpApiSearch("q").search()

    assert len(results) == 3
    assert results[0] == {"title": "A", "href": "https://a.example", "body": "sa"}
    assert results[1]["body"] == ""
    assert results[2]["title"] == ""


@patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
def test_serpapi_no_organic_results_returns_empty():
    with patch.object(_serpapi.requests, "get", return_value=_FakeResp({})):
        assert SerpApiSearch("q").search() == []
