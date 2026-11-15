"""Regression and unit tests for SearxSearch query_domains and max_results guards."""

import importlib.util
import json
import os
import pathlib
from unittest.mock import patch

# Import the module directly to avoid loading heavy optional dependencies
_SEARX_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher" / "retrievers" / "searx" / "searx.py"
)
_spec = importlib.util.spec_from_file_location("_searx_testmod", _SEARX_PATH)
_searx = importlib.util.module_from_spec(_spec)
with patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"}, clear=False):
    _spec.loader.exec_module(_searx)
SearxSearch = _searx.SearxSearch


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"})
def test_searx_query_domains_applied():
    payload = {"results": []}
    with patch.object(_searx.requests, "get", return_value=_FakeResp(payload)) as mock_get:
        SearxSearch("python async", query_domains=["docs.python.org", "github.com"]).search()

    assert mock_get.called
    sent_params = mock_get.call_args.kwargs["params"]
    assert sent_params["q"] == "(site:docs.python.org OR site:github.com) python async"
    assert sent_params["format"] == "json"


@patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"})
def test_searx_query_domains_empty_or_none():
    payload = {"results": []}
    with patch.object(_searx.requests, "get", return_value=_FakeResp(payload)) as mock_get:
        SearxSearch("python async", query_domains=[]).search()
    assert mock_get.call_args.kwargs["params"]["q"] == "python async"

    with patch.object(_searx.requests, "get", return_value=_FakeResp(payload)) as mock_get:
        SearxSearch("python async", query_domains=None).search()
    assert mock_get.call_args.kwargs["params"]["q"] == "python async"


@patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"})
def test_searx_query_domains_filters_empty_whitespace():
    payload = {"results": []}
    with patch.object(_searx.requests, "get", return_value=_FakeResp(payload)) as mock_get:
        SearxSearch("python async", query_domains=["", "   ", "example.com"]).search()
    assert mock_get.call_args.kwargs["params"]["q"] == "(site:example.com) python async"


@patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"})
def test_searx_max_results_non_positive_returns_empty_without_request():
    with patch.object(_searx.requests, "get") as mock_get:
        out_zero = SearxSearch("python async").search(max_results=0)
        out_neg = SearxSearch("python async").search(max_results=-5)

    assert out_zero == []
    assert out_neg == []
    assert not mock_get.called


@patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"})
def test_searx_preserves_title_when_present():
    payload = {
        "results": [
            {
                "url": "https://example.com/doc",
                "title": "Example Doc",
                "content": "Doc snippet"
            },
            {
                "url": "https://example.com/notitle",
                "content": "No title snippet"
            }
        ]
    }
    with patch.object(_searx.requests, "get", return_value=_FakeResp(payload)):
        results = SearxSearch("python async").search(max_results=10)

    assert len(results) == 2
    assert results[0] == {
        "href": "https://example.com/doc",
        "body": "Doc snippet",
        "title": "Example Doc"
    }
    assert results[1] == {
        "href": "https://example.com/notitle",
        "body": "No title snippet"
    }
