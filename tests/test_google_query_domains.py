"""Tests for GoogleSearch query_domains and max_results bounding."""

from __future__ import annotations

import importlib.util
import json
import pathlib
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "google"
    / "google.py"
)
_spec = importlib.util.spec_from_file_location("_google_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
GoogleSearch = _mod.GoogleSearch


class TestGoogleQueryDomains:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
        monkeypatch.setenv("GOOGLE_CX_KEY", "test-cx-key")

    def test_google_query_domains_applied(self):
        retriever = GoogleSearch(
            query="quantum computing",
            query_domains=["nature.com", "science.org"],
        )
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.text = json.dumps(
            {
                "items": [
                    {
                        "title": "Quantum Article",
                        "link": "https://nature.com/article1",
                        "snippet": "Snippet 1",
                    }
                ]
            }
        )

        with patch.object(_mod.requests, "get", return_value=fake_response) as mock_get:
            results = retriever.search(max_results=5)
            assert len(results) == 1
            assert results[0]["title"] == "Quantum Article"
            assert results[0]["href"] == "https://nature.com/article1"

            mock_get.assert_called_once()
            called_url = mock_get.call_args[0][0]
            parsed = parse_qs(urlparse(called_url).query)
            assert parsed["q"] == [
                "(site:nature.com OR site:science.org) quantum computing"
            ]

    def test_google_query_domains_filters_empty_whitespace(self):
        retriever = GoogleSearch(
            query="artificial intelligence",
            query_domains=["   ", "", "  arxiv.org  ", None, 123, "mit.edu"],
        )
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.text = json.dumps(
            {
                "items": [
                    {
                        "title": "AI Paper",
                        "link": "https://arxiv.org/abs/1234",
                        "snippet": "Paper abstract",
                    }
                ]
            }
        )

        with patch.object(_mod.requests, "get", return_value=fake_response) as mock_get:
            results = retriever.search(max_results=3)
            assert len(results) == 1

            mock_get.assert_called_once()
            called_url = mock_get.call_args[0][0]
            parsed = parse_qs(urlparse(called_url).query)
            assert parsed["q"] == [
                "(site:arxiv.org OR site:mit.edu) artificial intelligence"
            ]

    def test_google_query_domains_empty_or_none(self):
        retriever_none = GoogleSearch(query="test query", query_domains=None)
        retriever_empty = GoogleSearch(query="test query", query_domains=[])
        retriever_only_whitespace = GoogleSearch(
            query="test query", query_domains=["  ", ""]
        )

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.text = json.dumps({"items": []})

        with patch.object(_mod.requests, "get", return_value=fake_response) as mock_get:
            retriever_none.search(max_results=5)
            parsed_none = parse_qs(urlparse(mock_get.call_args[0][0]).query)
            assert parsed_none["q"] == ["test query"]

        with patch.object(_mod.requests, "get", return_value=fake_response) as mock_get:
            retriever_empty.search(max_results=5)
            parsed_empty = parse_qs(urlparse(mock_get.call_args[0][0]).query)
            assert parsed_empty["q"] == ["test query"]

        with patch.object(_mod.requests, "get", return_value=fake_response) as mock_get:
            retriever_only_whitespace.search(max_results=5)
            parsed_ws = parse_qs(urlparse(mock_get.call_args[0][0]).query)
            assert parsed_ws["q"] == ["test query"]

    def test_google_non_positive_max_results_returns_empty_without_request(self):
        retriever = GoogleSearch(query="test", query_domains=["example.com"])

        with patch.object(_mod.requests, "get") as mock_get:
            assert retriever.search(max_results=0) == []
            assert retriever.search(max_results=-5) == []
            mock_get.assert_not_called()

    def test_google_max_results_bounds_results(self):
        retriever = GoogleSearch(query="test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.text = json.dumps(
            {
                "items": [
                    {
                        "title": f"T{i}",
                        "link": f"https://example.com/{i}",
                        "snippet": f"S{i}",
                    }
                    for i in range(10)
                ]
            }
        )

        with patch.object(_mod.requests, "get", return_value=fake_response):
            results = retriever.search(max_results=3)
            assert len(results) == 3

    def test_google_skips_youtube_links(self):
        retriever = GoogleSearch(query="test")
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.text = json.dumps(
            {
                "items": [
                    {
                        "title": "Video 1",
                        "link": "https://www.youtube.com/watch?v=123",
                        "snippet": "Video",
                    },
                    {
                        "title": "Page 1",
                        "link": "https://example.com/page",
                        "snippet": "Page",
                    },
                ]
            }
        )

        with patch.object(_mod.requests, "get", return_value=fake_response):
            results = retriever.search(max_results=5)
            assert len(results) == 1
            assert results[0]["href"] == "https://example.com/page"
