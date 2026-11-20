"""Regression and unit tests for BingSearch query_domains and payload hardening."""

import importlib.util
import json
import os
import pathlib
from unittest.mock import patch

# Import the module directly to avoid loading heavy optional dependencies
_BING_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher" / "retrievers" / "bing" / "bing.py"
)
_spec = importlib.util.spec_from_file_location("_bing_testmod", _BING_PATH)
_bing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bing)
BingSearch = _bing.BingSearch


class _FakeResp:
    def __init__(self, payload):
        self.text = json.dumps(payload)

    def raise_for_status(self):
        return None


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bing_query_domains_applied():
    payload = {"webPages": {"value": []}}
    with patch.object(_bing.requests, "get", return_value=_FakeResp(payload)) as mock_get:
        BingSearch("python async", query_domains=["docs.python.org", "github.com"]).search()

    assert mock_get.called
    sent_params = mock_get.call_args.kwargs["params"]
    assert sent_params["q"] == "(site:docs.python.org OR site:github.com) python async"


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bing_query_domains_empty_or_none():
    payload = {"webPages": {"value": []}}
    with patch.object(_bing.requests, "get", return_value=_FakeResp(payload)) as mock_get:
        BingSearch("python async", query_domains=[]).search()
    assert mock_get.call_args.kwargs["params"]["q"] == "python async"

    with patch.object(_bing.requests, "get", return_value=_FakeResp(payload)) as mock_get:
        BingSearch("python async", query_domains=None).search()
    assert mock_get.call_args.kwargs["params"]["q"] == "python async"


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bing_null_webpages_returns_empty():
    # When Bing returns null for webPages, it must not raise AttributeError
    payload = {"webPages": None}
    with patch.object(_bing.requests, "get", return_value=_FakeResp(payload)):
        results = BingSearch("python async").search()
    assert results == []


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bing_skips_youtube_case_insensitive():
    payload = {
        "webPages": {
            "value": [
                {"name": "Valid Result", "url": "https://example.com/docs", "snippet": "Useful doc"},
                {"name": "YT Upper", "url": "https://www.YouTube.COM/watch?v=123", "snippet": "Video"},
                {"name": "YT Lower", "url": "https://youtube.com/watch?v=456", "snippet": "Video 2"},
            ]
        }
    }
    with patch.object(_bing.requests, "get", return_value=_FakeResp(payload)):
        results = BingSearch("python async").search()
    assert len(results) == 1
    assert results[0]["href"] == "https://example.com/docs"
    assert results[0]["title"] == "Valid Result"
