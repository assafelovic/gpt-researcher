"""TavilySearch must skip malformed sources instead of raising KeyError."""

from __future__ import annotations

from unittest.mock import patch

from gpt_researcher.retrievers.tavily.tavily_search import TavilySearch


def test_tavily_skips_sources_missing_url_or_non_dict():
    sources = [
        {"url": "https://a.example", "content": "ok"},
        {"content": "no url"},
        "not-a-dict",
        {"url": "https://b.example", "snippet": "from snippet"},
        {"url": None, "content": "null url"},
        {"url": "https://c.example", "content": None},
    ]

    searcher = TavilySearch.__new__(TavilySearch)
    searcher.query = "q"
    searcher.topic = "general"
    searcher.query_domains = None
    searcher.api_key = "fake"
    searcher.headers = {}
    searcher.base_url = "https://api.tavily.com/search"

    with patch.object(
        searcher,
        "_search",
        return_value={"results": sources},
    ):
        out = searcher.search(max_results=10)

    assert out == [
        {"href": "https://a.example", "body": "ok"},
        {"href": "https://b.example", "body": "from snippet"},
        {"href": "https://c.example", "body": ""},
    ]
