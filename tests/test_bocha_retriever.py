"""Tests for BoCha search retriever error handling."""
import json
import os
import sys
import importlib.util
import pytest
from unittest.mock import patch, MagicMock

# Import the module directly to avoid triggering the full gpt_researcher import chain
_spec = importlib.util.spec_from_file_location(
    "bocha",
    os.path.join(os.path.dirname(__file__), "..", "gpt_researcher", "retrievers", "bocha", "bocha.py"),
)
_bocha_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bocha_mod)
BoChaSearch = _bocha_mod.BoChaSearch


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("BOCHA_API_KEY", "test-key")


class TestBoChaSearch:
    def test_successful_search(self):
        """Verify normal search results are parsed correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "webPages": {
                    "value": [
                        {"name": "Result 1", "url": "https://example.com/1", "snippet": "Body 1"},
                        {"name": "Result 2", "url": "https://example.com/2", "snippet": "Body 2"},
                    ]
                }
            }
        }

        with patch.object(_bocha_mod.requests, "post", return_value=mock_response):
            searcher = BoChaSearch("test query")
            results = searcher.search(max_results=2)

        assert len(results) == 2
        assert results[0]["title"] == "Result 1"
        assert results[0]["href"] == "https://example.com/1"
        assert results[0]["body"] == "Body 1"

    def test_api_error_returns_empty_list(self):
        """When the API returns a non-200 status, search should return [] instead of crashing."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        with patch.object(_bocha_mod.requests, "post", return_value=mock_response):
            searcher = BoChaSearch("test query")
            results = searcher.search()

        assert results == []

    def test_malformed_json_returns_empty_list(self):
        """When the API returns invalid JSON, search should return [] instead of crashing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)

        with patch.object(_bocha_mod.requests, "post", return_value=mock_response):
            searcher = BoChaSearch("test query")
            results = searcher.search()

        assert results == []

    def test_missing_keys_returns_empty_list(self):
        """When response JSON is missing expected keys, search should return [] instead of crashing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "something went wrong"}

        with patch.object(_bocha_mod.requests, "post", return_value=mock_response):
            searcher = BoChaSearch("test query")
            results = searcher.search()

        assert results == []

    def test_network_error_returns_empty_list(self):
        """When the request fails due to network issues, search should return [] instead of crashing."""
        import requests as req

        with patch.object(_bocha_mod.requests, "post", side_effect=req.exceptions.ConnectionError("Connection refused")):
            searcher = BoChaSearch("test query")
            results = searcher.search()

        assert results == []

    def test_timeout_returns_empty_list(self):
        """When the request times out, search should return [] instead of crashing."""
        import requests as req

        with patch.object(_bocha_mod.requests, "post", side_effect=req.exceptions.Timeout("Request timed out")):
            searcher = BoChaSearch("test query")
            results = searcher.search()

        assert results == []

    def test_missing_api_key_raises(self):
        """When BOCHA_API_KEY is not set, constructor should raise with a helpful message."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="BOCHA_API_KEY"):
                BoChaSearch("test query")

    def test_partial_result_fields(self):
        """When result items are missing some fields, search should use empty strings as defaults."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "webPages": {
                    "value": [
                        {"name": "Only Title"},
                    ]
                }
            }
        }

        with patch.object(_bocha_mod.requests, "post", return_value=mock_response):
            searcher = BoChaSearch("test query")
            results = searcher.search()

        assert len(results) == 1
        assert results[0]["title"] == "Only Title"
        assert results[0]["href"] == ""
        assert results[0]["body"] == ""
