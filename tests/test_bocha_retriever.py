"""Regression and unit tests for BoChaSearch retriever.

Validates that:
1. Missing BOCHA_API_KEY environment variable raises an informative Exception with setup guidance.
2. Search normalizes webPages.value into [{"title": ..., "href": ..., "body": ...}] format.
3. Malformed results (non-dict items, missing/empty url) are skipped gracefully.
4. Missing title or snippet fields default to empty strings without crashing.
5. Network failures and HTTP errors degrade to an empty list rather than escaping.
"""
import importlib.util
import os
import pathlib
from unittest.mock import patch

import pytest

# Import module directly to avoid heavy optional dependencies during testing
_BOCHA_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher" / "retrievers" / "bocha" / "bocha.py"
)
_spec = importlib.util.spec_from_file_location("_bocha_under_test", _BOCHA_PATH)
_bocha = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bocha)
BoChaSearch = _bocha.BoChaSearch


class _FakeResp:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise _bocha.requests.RequestException(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


def test_missing_api_key_raises_clear_error():
    with patch.dict(os.environ, {}, clear=True), pytest.raises(Exception, match=r"BOCHA_API_KEY"):
        BoChaSearch("test query")


def test_get_api_key_returns_key():
    with patch.dict(os.environ, {"BOCHA_API_KEY": "test-bocha-key"}):
        searcher = BoChaSearch("test query")
        assert searcher.api_key == "test-bocha-key"


@patch.dict(os.environ, {"BOCHA_API_KEY": "test-bocha-key"})
def test_search_normalizes_results():
    payload = {
        "data": {
            "webPages": {
                "value": [
                    {
                        "name": "Result One",
                        "url": "https://example.com/one",
                        "snippet": "First snippet content",
                    },
                    {
                        "name": "Result Two",
                        "url": "https://example.com/two",
                        "snippet": "Second snippet content",
                    },
                ]
            }
        }
    }
    with patch.object(_bocha.requests, "post", return_value=_FakeResp(payload)) as mock_post:
        results = BoChaSearch("ai agents").search(max_results=5)

    assert len(results) == 2
    assert results[0] == {
        "title": "Result One",
        "href": "https://example.com/one",
        "body": "First snippet content",
    }
    assert results[1] == {
        "title": "Result Two",
        "href": "https://example.com/two",
        "body": "Second snippet content",
    }
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["timeout"] == 10
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-bocha-key"


@patch.dict(os.environ, {"BOCHA_API_KEY": "test-bocha-key"})
def test_search_skips_non_dict_and_empty_url():
    payload = {
        "data": {
            "webPages": {
                "value": [
                    "not-a-dict",
                    None,
                    {"name": "No URL", "snippet": "missing url"},
                    {"name": "Empty URL", "url": "", "snippet": "empty url"},
                    {"name": "Valid", "url": "https://valid.example", "snippet": "valid snippet"},
                ]
            }
        }
    }
    with patch.object(_bocha.requests, "post", return_value=_FakeResp(payload)):
        results = BoChaSearch("query").search()

    assert results == [
        {"title": "Valid", "href": "https://valid.example", "body": "valid snippet"},
    ]


@patch.dict(os.environ, {"BOCHA_API_KEY": "test-bocha-key"})
def test_search_handles_missing_keys_gracefully():
    payload = {
        "data": {
            "webPages": {
                "value": [
                    {"url": "https://no-name.example", "snippet": "has snippet"},
                    {"name": "No Snippet", "url": "https://no-snippet.example"},
                ]
            }
        }
    }
    with patch.object(_bocha.requests, "post", return_value=_FakeResp(payload)):
        results = BoChaSearch("query").search()

    assert len(results) == 2
    assert results[0] == {"title": "", "href": "https://no-name.example", "body": "has snippet"}
    assert results[1] == {"title": "No Snippet", "href": "https://no-snippet.example", "body": ""}


@patch.dict(os.environ, {"BOCHA_API_KEY": "test-bocha-key"})
def test_search_empty_or_malformed_payload_returns_empty():
    malformed_payloads = [
        None,
        {},
        {"data": None},
        {"data": {"webPages": None}},
        {"data": {"webPages": {"value": None}}},
        {"data": {"webPages": {"value": "not-a-list"}}},
    ]
    for malformed in malformed_payloads:
        with patch.object(_bocha.requests, "post", return_value=_FakeResp(malformed)):
            assert BoChaSearch("query").search() == []


@patch.dict(os.environ, {"BOCHA_API_KEY": "test-bocha-key"})
def test_search_request_exception_returns_empty():
    with patch.object(_bocha.requests, "post", side_effect=_bocha.requests.RequestException("connection failed")):
        assert BoChaSearch("query").search() == []


@patch.dict(os.environ, {"BOCHA_API_KEY": "test-bocha-key"})
def test_search_http_error_returns_empty():
    with patch.object(_bocha.requests, "post", return_value=_FakeResp({}, status_code=500)):
        assert BoChaSearch("query").search() == []
