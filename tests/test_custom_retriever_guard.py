"""CustomRetriever.search must always return a list, never None."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.custom.custom import CustomRetriever


def _make(endpoint="https://example.test/search"):
    with patch.dict("os.environ", {"RETRIEVER_ENDPOINT": endpoint}, clear=False):
        return CustomRetriever(query="q")


def test_custom_returns_empty_list_on_http_error():
    c = _make()
    resp = MagicMock()
    resp.raise_for_status.side_effect = Exception("boom")
    # Use requests.RequestException path
    import requests

    resp.raise_for_status.side_effect = requests.HTTPError("boom")
    with patch("gpt_researcher.retrievers.custom.custom.requests.get", return_value=resp):
        out = c.search()
    assert out == []


def test_custom_returns_empty_list_on_null_json():
    c = _make()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = None
    with patch("gpt_researcher.retrievers.custom.custom.requests.get", return_value=resp):
        out = c.search()
    assert out == []


def test_custom_returns_empty_list_on_non_list_json():
    c = _make()
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"url": "x"}
    with patch("gpt_researcher.retrievers.custom.custom.requests.get", return_value=resp):
        out = c.search()
    assert out == []


def test_custom_returns_list_payload():
    c = _make()
    payload = [{"url": "https://a", "raw_content": "hi"}]
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    with patch("gpt_researcher.retrievers.custom.custom.requests.get", return_value=resp) as get:
        out = c.search()
    assert out == payload
    # timeout is passed so the retriever cannot hang forever
    assert get.call_args.kwargs.get("timeout") == 20
