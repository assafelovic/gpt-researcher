"""CustomRetriever.search must always return a clean list of dict results."""

from __future__ import annotations

import importlib.util
import pathlib
from unittest.mock import MagicMock, patch

import requests

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "custom"
    / "custom.py"
)
_spec = importlib.util.spec_from_file_location("_custom_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CustomRetriever = _mod.CustomRetriever


def _make(endpoint="https://example.test/search"):
    with patch.dict("os.environ", {"RETRIEVER_ENDPOINT": endpoint}, clear=False):
        return CustomRetriever(query="q")


def test_custom_returns_empty_list_on_http_error():
    c = _make()
    resp = MagicMock()
    resp.raise_for_status.side_effect = requests.HTTPError("boom")
    with patch.object(_mod.requests, "get", return_value=resp):
        out = c.search()
    assert out == []


def test_custom_returns_empty_list_on_null_json():
    c = _make()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = None
    with patch.object(_mod.requests, "get", return_value=resp):
        out = c.search()
    assert out == []


def test_custom_returns_empty_list_on_non_list_json():
    c = _make()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"url": "x"}
    with patch.object(_mod.requests, "get", return_value=resp):
        out = c.search()
    assert out == []


def test_custom_returns_list_payload():
    c = _make()
    payload = [{"url": "https://a", "raw_content": "hi"}]
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    with patch.object(_mod.requests, "get", return_value=resp) as get:
        out = c.search()
    assert out == payload
    assert get.call_args.kwargs.get("timeout") == 20


def test_custom_skips_non_dict_and_url_less_items():
    c = _make()
    payload = [
        "not-a-dict",
        None,
        {"raw_content": "no url"},
        {"url": "https://ok.example", "raw_content": "body"},
        {"href": "https://alt.example", "body": "alt body"},
    ]
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    with patch.object(_mod.requests, "get", return_value=resp):
        out = c.search()
    assert out == [
        {"url": "https://ok.example", "raw_content": "body"},
        {"url": "https://alt.example", "raw_content": "alt body"},
    ]
