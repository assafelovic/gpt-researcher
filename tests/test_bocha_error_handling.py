"""Regression tests for BoChaSearch robustness.

Unlike every sibling retriever (which returns ``[]`` and uses ``.get()`` on a
bad/empty payload), BoChaSearch used to index wrapper keys diectly and crash.
Today network/JSON errors return []; this suite also guards non-dict value rows.
"""

import importlib.util
import os
import pathlib
from unittest.mock import MagicMock, patch

import requests

_BOCHA_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "bocha"
    / "bocha.py"
)
_spec = importlib.util.spec_from_file_location("_bocha_under_test", _BOCHA_PATH)
_bocha = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bocha)
BoChaSearch = _bocha.BoChaSearch


def _make_search():
    with patch.dict(os.environ, {"BOCHA_API_KEY": "test-key"}):
        return BoChaSearch("test query")


def test_missing_keys_returns_empty_list():
    search = _make_search()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"unexpected": "shape"}  # no data.webPages.value

    with patch.object(_bocha.requests, "post", return_value=resp):
        assert search.search() == []


def test_request_exception_returns_empty_list():
    search = _make_search()
    with patch.object(
        _bocha.requests,
        "post",
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

    with patch.object(_bocha.requests, "post", return_value=resp):
        results = search.search()

    assert results == [
        {"title": "T", "href": "https://e.com", "body": "B"},
        {"title": "T2", "href": "https://e2.com", "body": ""},
    ]


def test_bocha_skips_non_dict_and_empty_url():
    search = _make_search()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "data": {
            "webPages": {
                "value": [
                    "not-a-dict",
                    None,
                    {"name": "No URL"},
                    {"name": "Ok", "url": "https://ok.example", "snippet": "body"},
                ]
            }
        }
    }

    with patch.object(_bocha.requests, "post", return_value=resp):
        results = search.search()

    assert results == [
        {"title": "Ok", "href": "https://ok.example", "body": "body"},
    ]
