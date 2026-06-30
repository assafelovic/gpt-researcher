"""Regression tests for BoChaSearch robustness.

Unlike every sibling retriever (which returns ``[]`` and uses ``.get()`` on a
bad/empty payload), BoChaSearch indexed ``json_response["data"]["webPages"]
["value"]`` directly and had no error handling. A non-200 response, a body
that doesn't decode as JSON, or a payload missing those keys crashed the whole
research run with an unhandled ``KeyError`` / ``JSONDecodeError``.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


def _make_search():
    with patch.dict(os.environ, {"BOCHA_API_KEY": "test-key"}):
        from gpt_researcher.retrievers.bocha.bocha import BoChaSearch

        return BoChaSearch("test query")


def test_missing_keys_returns_empty_list():
    search = _make_search()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"unexpected": "shape"}  # no data.webPages.value

    with patch(
        "gpt_researcher.retrievers.bocha.bocha.requests.post", return_value=resp
    ):
        assert search.search() == []


def test_request_exception_returns_empty_list():
    import requests

    search = _make_search()
    with patch(
        "gpt_researcher.retrievers.bocha.bocha.requests.post",
        side_effect=requests.RequestException("boom"),
    ):
        assert search.search() == []


def test_valid_payload_is_normalized():
    search = _make_search()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "data": {
            "webPages": {
                "value": [
                    {"name": "T", "url": "https://e.com", "snippet": "B"},
                    {"name": "T2", "url": "https://e2.com"},  # missing snippet
                ]
            }
        }
    }

    with patch(
        "gpt_researcher.retrievers.bocha.bocha.requests.post", return_value=resp
    ):
        results = search.search()

    assert results == [
        {"title": "T", "href": "https://e.com", "body": "B"},
        {"title": "T2", "href": "https://e2.com", "body": ""},
    ]
