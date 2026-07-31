"""Tests for the Firecrawl search retriever (HLT addition)."""
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gpt_researcher.retrievers.firecrawl.firecrawl_search import FirecrawlSearch


def test_search_maps_results(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    monkeypatch.delenv("FIRECRAWL_SERVER_URL", raising=False)

    response = MagicMock()
    response.json.return_value = {
        "success": True,
        "data": [
            {"url": "https://example.com/a", "description": "About A", "title": "A"},
            {"url": "https://example.com/b", "markdown": "Full B content"},
            {"title": "no url, skipped"},
        ],
    }
    with patch("requests.post", return_value=response) as post:
        results = FirecrawlSearch("test query").search(max_results=5)

    assert results == [
        {"href": "https://example.com/a", "body": "About A"},
        {"href": "https://example.com/b", "body": "Full B content"},
    ]
    args, kwargs = post.call_args
    assert args[0] == "https://api.firecrawl.dev/v1/search"
    assert kwargs["headers"]["Authorization"] == "Bearer fc-test"


def test_search_restricts_domains(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")

    response = MagicMock()
    response.json.return_value = {"data": []}
    with patch("requests.post", return_value=response) as post:
        FirecrawlSearch("query", query_domains=["github.com"]).search()

    assert "site:github.com" in post.call_args.kwargs["data"]


def test_search_without_key_returns_empty(monkeypatch):
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    assert FirecrawlSearch("query").search() == []


def test_firecrawl_registered_as_retriever():
    from gpt_researcher.actions.retriever import get_retriever
    from gpt_researcher.retrievers.utils import get_all_retriever_names

    assert get_retriever("firecrawl") is FirecrawlSearch
    assert "firecrawl" in get_all_retriever_names()
