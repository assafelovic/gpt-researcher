"""Regression tests for SearchApiSearch result normalization.

Without the fix, a response missing ``organic_results`` raises a KeyError,
and a single result missing ``title``/``link``/``snippet`` raises a KeyError
that aborts the whole ``search()`` call via the broad except — dropping every
other valid hit on the page.
"""
import importlib.util
import os
import pathlib
from unittest.mock import patch

_SEARCHAPI_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher" / "retrievers" / "searchapi" / "searchapi.py"
)
_spec = importlib.util.spec_from_file_location("_searchapi_under_test", _SEARCHAPI_PATH)
_searchapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_searchapi)
SearchApiSearch = _searchapi.SearchApiSearch


class _FakeResp:
    def __init__(self, payload, status_code=200):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


@patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"})
def test_searchapi_skips_results_missing_keys():
    payload = {
        "organic_results": [
            {"title": "A", "link": "https://a.example", "snippet": "sa"},
            {"title": "B", "link": "https://b.example"},  # missing snippet
            {"link": "https://c.example"},  # missing title + snippet
            {"title": "D", "snippet": "sd"},  # missing link -> skipped
            "not-a-dict",
        ]
    }
    with patch.object(_searchapi.requests, "get", return_value=_FakeResp(payload)):
        results = SearchApiSearch("q").search()

    assert len(results) == 3
    assert results[0] == {"title": "A", "href": "https://a.example", "body": "sa"}
    assert results[1] == {"title": "B", "href": "https://b.example", "body": ""}
    assert results[2] == {"title": "", "href": "https://c.example", "body": ""}


@patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"})
def test_searchapi_no_organic_results_returns_empty():
    with patch.object(_searchapi.requests, "get", return_value=_FakeResp({})):
        assert SearchApiSearch("q").search() == []


@patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"})
def test_searchapi_null_organic_results_returns_empty():
    with patch.object(
        _searchapi.requests, "get", return_value=_FakeResp({"organic_results": None})
    ):
        assert SearchApiSearch("q").search() == []


@patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"})
def test_searchapi_skips_youtube_links():
    payload = {
        "organic_results": [
            {"title": "YT", "link": "https://www.youtube.com/watch?v=x", "snippet": "v"},
            {"title": "OK", "link": "https://ok.example", "snippet": "body"},
        ]
    }
    with patch.object(_searchapi.requests, "get", return_value=_FakeResp(payload)):
        results = SearchApiSearch("q").search()
    assert results == [{"title": "OK", "href": "https://ok.example", "body": "body"}]
