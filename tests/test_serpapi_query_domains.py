"""Tests for SerpApiSearch query_domains and max_results bounding."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import urllib.parse
from unittest.mock import MagicMock, patch

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "serpapi"
    / "serpapi.py"
)
_spec = importlib.util.spec_from_file_location("_serpapi_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SerpApiSearch = _mod.SerpApiSearch


def _extract_query_param(mock_get: MagicMock) -> str:
    called_url = mock_get.call_args[0][0]
    parsed = urllib.parse.urlparse(called_url)
    qs = urllib.parse.parse_qs(parsed.query)
    return qs.get("q", [""])[0]


class TestSerpApiQueryDomains:
    @patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
    @patch.object(_mod.requests, "get")
    def test_serpapi_query_domains_applied(self, mock_get):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"organic_results": []}
        mock_get.return_value = mock_resp

        retriever = SerpApiSearch(
            "artificial intelligence",
            query_domains=["nature.com", "science.org"],
        )
        retriever.search(max_results=5)

        mock_get.assert_called_once()
        sent_q = _extract_query_param(mock_get)
        assert sent_q == "(site:nature.com OR site:science.org) artificial intelligence"

    @patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
    @patch.object(_mod.requests, "get")
    def test_serpapi_query_domains_filters_empty_whitespace(self, mock_get):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"organic_results": []}
        mock_get.return_value = mock_resp

        retriever = SerpApiSearch(
            "test query",
            query_domains=["", "   ", "example.com", None, 123],
        )
        retriever.search(max_results=5)

        mock_get.assert_called_once()
        sent_q = _extract_query_param(mock_get)
        assert sent_q == "(site:example.com) test query"

    @patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
    @patch.object(_mod.requests, "get")
    def test_serpapi_query_domains_empty_or_none(self, mock_get):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"organic_results": []}
        mock_get.return_value = mock_resp

        retriever = SerpApiSearch("plain query", query_domains=[])
        retriever.search(max_results=5)

        mock_get.assert_called_once()
        sent_q = _extract_query_param(mock_get)
        assert sent_q == "plain query"

    @patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
    @patch.object(_mod.requests, "get")
    def test_serpapi_non_positive_max_results_returns_empty_without_request(
        self, mock_get
    ):
        retriever = SerpApiSearch("test query")
        assert retriever.search(max_results=0) == []
        assert retriever.search(max_results=-5) == []
        mock_get.assert_not_called()

    @patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
    @patch.object(_mod.requests, "get")
    def test_serpapi_max_results_bounds_results(self, mock_get):
        payload = {
            "organic_results": [
                {
                    "title": f"Title {i}",
                    "link": f"https://example.com/{i}",
                    "snippet": f"Snippet {i}",
                }
                for i in range(10)
            ]
        }
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = payload
        mock_get.return_value = mock_resp

        retriever = SerpApiSearch("test query")
        results = retriever.search(max_results=3)

        assert len(results) == 3
        assert [r["title"] for r in results] == ["Title 0", "Title 1", "Title 2"]
