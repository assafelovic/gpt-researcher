"""Regression and unit tests for BraveSearch query_domains and parameter handling."""

import os
import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.brave.brave import BraveSearch


class TestBraveQueryDomains(unittest.TestCase):
    @patch("gpt_researcher.retrievers.brave.brave.requests.get")
    def test_brave_query_domains_applied(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key"}):
            BraveSearch(
                "python async",
                query_domains=["docs.python.org", "github.com"],
            ).search()

        self.assertTrue(mock_get.called)
        sent_params = mock_get.call_args.kwargs["params"]
        self.assertEqual(
            sent_params["q"],
            "(site:docs.python.org OR site:github.com) python async",
        )

    @patch("gpt_researcher.retrievers.brave.brave.requests.get")
    def test_brave_query_domains_empty_or_none(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key"}):
            BraveSearch("python async", query_domains=[]).search()
        self.assertEqual(mock_get.call_args.kwargs["params"]["q"], "python async")

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key"}):
            BraveSearch("python async", query_domains=None).search()
        self.assertEqual(mock_get.call_args.kwargs["params"]["q"], "python async")

    @patch("gpt_researcher.retrievers.brave.brave.requests.get")
    def test_brave_query_domains_filters_empty_strings(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key"}):
            BraveSearch(
                "python async",
                query_domains=["", "   ", "example.com"],
            ).search()
        self.assertEqual(
            mock_get.call_args.kwargs["params"]["q"],
            "(site:example.com) python async",
        )

    @patch("gpt_researcher.retrievers.brave.brave.requests.get")
    def test_brave_non_positive_max_results_returns_empty(self, mock_get):
        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key"}):
            results = BraveSearch("python async").search(max_results=0)
            self.assertEqual(results, [])
            results_neg = BraveSearch("python async").search(max_results=-1)
            self.assertEqual(results_neg, [])
        mock_get.assert_not_called()
