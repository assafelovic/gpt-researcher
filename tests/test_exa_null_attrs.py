"""ExaSearch must skip hits with missing url/id rather than raising."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.exa.exa import ExaSearch


def _searcher():
    # bypass __init__ pkg/API setup
    s = ExaSearch.__new__(ExaSearch)
    s.query = "q"
    s.query_domains = None
    s.api_key = "k"
    s.client = MagicMock()
    return s


def test_search_skips_missing_url_and_uses_summary_fallback():
    s = _searcher()
    s.client.search.return_value = SimpleNamespace(
        results=[
            SimpleNamespace(url="https://a.example", text="body a"),
            SimpleNamespace(url=None, text="orphan"),
            SimpleNamespace(url="https://b.example", text=None, summary="sum b"),
        ]
    )
    out = s.search(max_results=5)
    assert out == [
        {"href": "https://a.example", "body": "body a"},
        {"href": "https://b.example", "body": "sum b"},
    ]


def test_find_similar_skips_missing_url():
    s = _searcher()
    s.client.find_similar.return_value = SimpleNamespace(
        results=[SimpleNamespace(url="", text="x"), SimpleNamespace(url="https://c", text="y")]
    )
    assert s.find_similar("https://seed") == [{"href": "https://c", "body": "y"}]


def test_get_contents_skips_missing_id():
    s = _searcher()
    s.client.get_contents.return_value = SimpleNamespace(
        results=[
            SimpleNamespace(id="1", text="t"),
            SimpleNamespace(id=None, text="nope"),
        ]
    )
    assert s.get_contents(["1"]) == [{"id": "1", "content": "t"}]
