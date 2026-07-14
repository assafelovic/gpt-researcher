"""Ensure TavilySearch normalizes significantly-malformed result rows."""
from unittest.mock import patch

from gpt_researcher.retrievers.tavily.tavily_search import TavilySearch


@patch.dict("os.environ", {"TAVILY_API_KEY": "k"}, clear=False)
def test_tavily_skips_malformed_items():
    searcher = TavilySearch("q")
    with patch.object(
        searcher,
        "_search",
        return_value={
            "results": [
                None,
                "bad",
                {"content": "no-url"},
                {"url": "https://ok", "content": "body"},
                {"href": "https://href", "snippet": "snip"},
            ]
        },
    ):
        out = searcher.search()
    assert out == [
        {"href": "https://ok", "body": "body"},
        {"href": "https://href", "body": "snip"},
    ]
