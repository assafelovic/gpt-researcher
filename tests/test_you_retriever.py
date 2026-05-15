"""Unit tests for the You.com Search retriever.

These tests stub out ``requests.get`` so no network or live API key is
required. The fixture payload mirrors the shape captured at
``research/fixtures/search-response.json`` in the youcom-ecosystem-work
companion repo.
"""

import importlib.util
import os
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests


# Load the retriever module directly from disk to avoid pulling in the
# whole ``gpt_researcher`` package (and its many optional dependencies)
# at unit-test time.
_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "you"
    / "you_search.py"
)
_spec = importlib.util.spec_from_file_location(
    "you_search_under_test", _MODULE_PATH
)
you_search = importlib.util.module_from_spec(_spec)
sys.modules["you_search_under_test"] = you_search
_spec.loader.exec_module(you_search)

BASE_URL = you_search.BASE_URL
YouSearch = you_search.YouSearch


# Reduced fixture mirroring fixtures/search-response.json
SEARCH_FIXTURE = {
    "results": {
        "web": [
            {
                "url": "https://docs.langchain.com/oss/python/integrations/providers/overview",
                "title": "LangChain Python integrations - Docs by LangChain",
                "description": "Integrate with providers using LangChain Python.",
                "snippets": [
                    "LangChain offers an extensive ecosystem with 1000+ integrations.",
                    "Community integrations can be found in langchain-community.",
                ],
            },
            {
                "url": "https://docs.langchain.com/oss/python/integrations/providers/all_providers",
                "title": "All LangChain Python integration providers - Docs by LangChain",
                "description": "Browse the complete collection of integrations available for Python.",
                "snippets": [
                    "LangChain Python offers the most extensive ecosystem.",
                ],
            },
        ]
    },
    "metadata": {
        "query": "python langchain integration",
        "search_uuid": "46e1a6fa-ad87-485e-9b99-e18db4c40c5b",
        "latency": 0.53,
    },
}


def _mock_response(payload, status_code=200):
    """Build a MagicMock that quacks like a ``requests.Response``."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = payload
    return mock


class YouSearchTests(unittest.TestCase):
    def setUp(self):
        # Ensure no environment leakage between tests.
        self._env_backup = {
            key: os.environ.pop(key, None)
            for key in ("YOU_API_KEY", "YOU_COUNTRY", "YOU_SAFE_SEARCH")
        }

    def tearDown(self):
        for key, value in self._env_backup.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    @patch("you_search_under_test.requests.get")
    def test_search_returns_results_in_tavily_shape(self, mock_get):
        os.environ["YOU_API_KEY"] = "test-key"
        mock_get.return_value = _mock_response(SEARCH_FIXTURE)

        results = YouSearch("python langchain integration").search(max_results=2)

        self.assertEqual(len(results), 2)
        for item in results:
            self.assertEqual(set(item.keys()), {"href", "body", "title"})
        self.assertEqual(
            results[0]["href"],
            "https://docs.langchain.com/oss/python/integrations/providers/overview",
        )
        self.assertIn("LangChain offers", results[0]["body"])
        self.assertEqual(
            results[0]["title"],
            "LangChain Python integrations - Docs by LangChain",
        )

        # Verify the request URL and headers
        call = mock_get.call_args
        self.assertEqual(call.args[0], BASE_URL)
        self.assertEqual(call.kwargs["headers"], {"X-API-Key": "test-key"})
        self.assertEqual(call.kwargs["params"]["query"], "python langchain integration")
        self.assertEqual(call.kwargs["params"]["count"], 2)

    @patch("you_search_under_test.requests.get")
    def test_search_soft_fails_on_missing_key(self, mock_get):
        # No env var, no header
        with self.assertLogs(
            "you_search_under_test", level="WARNING"
        ) as captured:
            results = YouSearch("anything").search()

        self.assertEqual(results, [])
        mock_get.assert_not_called()
        self.assertTrue(
            any("YOU_API_KEY" in record for record in captured.output),
            f"Expected warning to mention YOU_API_KEY; got {captured.output!r}",
        )

    @patch("you_search_under_test.requests.get")
    def test_search_uses_header_key_over_env(self, mock_get):
        os.environ["YOU_API_KEY"] = "env-key"
        mock_get.return_value = _mock_response(SEARCH_FIXTURE)

        retriever = YouSearch("q", headers={"you_api_key": "header-key"})
        retriever.search(max_results=1)

        self.assertEqual(
            mock_get.call_args.kwargs["headers"],
            {"X-API-Key": "header-key"},
        )

    @patch("you_search_under_test.requests.get")
    def test_search_propagates_locale(self, mock_get):
        os.environ["YOU_API_KEY"] = "test-key"
        mock_get.return_value = _mock_response(SEARCH_FIXTURE)

        retriever = YouSearch("q", country="SA", language="ar")
        retriever.search(max_results=3)

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["country"], "SA")
        self.assertEqual(params["search_lang"], "ar")

    @patch("you_search_under_test.requests.get")
    def test_search_returns_empty_on_timeout(self, mock_get):
        os.environ["YOU_API_KEY"] = "test-key"
        mock_get.side_effect = requests.exceptions.Timeout("slow")

        results = YouSearch("q").search()

        self.assertEqual(results, [])

    @patch("you_search_under_test.requests.get")
    def test_search_returns_empty_on_http_error(self, mock_get):
        os.environ["YOU_API_KEY"] = "test-key"
        mock_get.return_value = _mock_response({"error": "rate limited"}, status_code=429)

        results = YouSearch("q").search()

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
