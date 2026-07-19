"""TavilySearch.search must not AttributeError on non-dict API JSON."""

import importlib.util
import pathlib
from unittest.mock import patch

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "tavily"
    / "tavily_search.py"
)
_spec = importlib.util.spec_from_file_location("_tavily_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
TavilySearch = _mod.TavilySearch


def test_search_returns_empty_when_api_json_is_list():
    s = TavilySearch("q", headers={"tavily_api_key": "k"})
    with patch.object(s, "_search", return_value=[{"url": "https://x"}]):
        assert s.search() == []


def test_search_returns_empty_when_results_not_list():
    s = TavilySearch("q", headers={"tavily_api_key": "k"})
    with patch.object(s, "_search", return_value={"results": {"url": "https://x"}}):
        assert s.search() == []


def test_search_normalizes_dict_hits():
    s = TavilySearch("q", headers={"tavily_api_key": "k"})
    payload = {
        "results": [
            {"url": "https://a.example", "content": "body-a"},
            "skip",
            {"content": "no-url"},
            {"url": "https://b.example", "snippet": "body-b"},
        ]
    }
    with patch.object(s, "_search", return_value=payload):
        assert s.search() == [
            {"href": "https://a.example", "body": "body-a"},
            {"href": "https://b.example", "body": "body-b"},
        ]
