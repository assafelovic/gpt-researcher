"""Serper organic items must not KeyError on partial payloads."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.serper.serper import SerperSearch


def test_skip_items_missing_link(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    resp = MagicMock()
    resp.text = '{"organic":[{"title":"t","snippet":"s"},{"title":"ok","link":"https://e.example","snippet":"body"}]}'
    with patch("requests.request", return_value=resp):
        out = SerperSearch("q").search()
    assert out == [
        {"title": "ok", "href": "https://e.example", "body": "body"}
    ]


def test_organic_not_list_returns_empty(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    resp = MagicMock()
    resp.text = '{"organic":"nope"}'
    with patch("requests.request", return_value=resp):
        assert SerperSearch("q").search() == []
