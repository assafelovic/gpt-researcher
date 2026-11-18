"""Tests for SerperSearch query_domains and max_results bounding."""

from __future__ import annotations

import importlib.util
import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "serper"
    / "serper.py"
)
_spec = importlib.util.spec_from_file_location("_serper_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SerperSearch = _mod.SerperSearch


class TestSerperQueryDomains:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("SERPER_API_KEY", "test-api-key")

    def test_serper_query_domains_applied(self):
        retriever = SerperSearch(
            query="quantum computing",
            query_domains=["nature.com", "science.org"],
        )
        fake_response = MagicMock()
        fake_response.text = json.dumps(
            {
                "organic": [
                    {
                        "title": "Quantum Article",
                        "link": "https://nature.com/article1",
                        "snippet": "Snippet 1",
                    }
                ]
            }
        )

        with patch.object(
            _mod.requests, "request", return_value=fake_response
        ) as mock_req:
            results = retriever.search(max_results=5)
            assert len(results) == 1
            assert results[0]["title"] == "Quantum Article"
            assert results[0]["href"] == "https://nature.com/article1"

            mock_req.assert_called_once()
            _, kwargs = mock_req.call_args
            payload = json.loads(kwargs["data"])
            assert (
                payload["q"]
                == "(site:nature.com OR site:science.org) quantum computing"
            )
            assert payload["num"] == 5

    def test_serper_query_domains_filters_empty_whitespace(self):
        retriever = SerperSearch(
            query="artificial intelligence",
            query_domains=["   ", "", "  arxiv.org  ", None, 123, "mit.edu"],
        )
        fake_response = MagicMock()
        fake_response.text = json.dumps(
            {
                "organic": [
                    {
                        "title": "AI Paper",
                        "link": "https://arxiv.org/abs/1234",
                        "snippet": "Paper abstract",
                    }
                ]
            }
        )

        with patch.object(
            _mod.requests, "request", return_value=fake_response
        ) as mock_req:
            results = retriever.search(max_results=3)
            assert len(results) == 1

            mock_req.assert_called_once()
            _, kwargs = mock_req.call_args
            payload = json.loads(kwargs["data"])
            assert (
                payload["q"]
                == "(site:arxiv.org OR site:mit.edu) artificial intelligence"
            )

    def test_serper_query_domains_empty_or_none(self):
        retriever_none = SerperSearch(query="test query", query_domains=None)
        retriever_empty = SerperSearch(query="test query", query_domains=[])

        fake_response = MagicMock()
        fake_response.text = json.dumps({"organic": []})

        with patch.object(
            _mod.requests, "request", return_value=fake_response
        ) as mock_req:
            retriever_none.search(max_results=5)
            payload_none = json.loads(mock_req.call_args[1]["data"])
            assert payload_none["q"] == "test query"

        with patch.object(
            _mod.requests, "request", return_value=fake_response
        ) as mock_req:
            retriever_empty.search(max_results=5)
            payload_empty = json.loads(mock_req.call_args[1]["data"])
            assert payload_empty["q"] == "test query"

    def test_serper_non_positive_max_results_returns_empty_without_request(self):
        retriever = SerperSearch(query="test", query_domains=["example.com"])

        with patch.object(_mod.requests, "request") as mock_req:
            assert retriever.search(max_results=0) == []
            assert retriever.search(max_results=-5) == []
            mock_req.assert_not_called()

    def test_serper_max_results_bounds_results(self):
        retriever = SerperSearch(query="test")
        fake_response = MagicMock()
        fake_response.text = json.dumps(
            {
                "organic": [
                    {
                        "title": f"T{i}",
                        "link": f"https://example.com/{i}",
                        "snippet": f"S{i}",
                    }
                    for i in range(10)
                ]
            }
        )

        with patch.object(_mod.requests, "request", return_value=fake_response):
            results = retriever.search(max_results=3)
            assert len(results) == 3

    def test_serper_exclude_sites_and_query_domains(self):
        retriever = SerperSearch(
            query="python guide",
            query_domains=["realpython.com", "docs.python.org"],
            exclude_sites=["spam.com", "ad.com"],
        )
        fake_response = MagicMock()
        fake_response.text = json.dumps({"organic": []})

        with patch.object(
            _mod.requests, "request", return_value=fake_response
        ) as mock_req:
            retriever.search(max_results=5)
            payload = json.loads(mock_req.call_args[1]["data"])
            assert (
                payload["q"]
                == "(site:realpython.com OR site:docs.python.org) python guide -site:spam.com -site:ad.com"
            )
