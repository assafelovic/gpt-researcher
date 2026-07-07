import os
import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.nimble.nimble_search import NimbleSearch


class TestNimbleSearch(unittest.TestCase):
    def test_missing_api_key_defaults_to_blank(self):
        with patch.dict(os.environ, {}, clear=True):
            retriever = NimbleSearch("test query")
        self.assertEqual(retriever.api_key, "")

    @patch("gpt_researcher.retrievers.nimble.nimble_search.requests.post")
    def test_search_normalizes_results(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/one",
                    "title": "One",
                    "content": "First snippet",
                },
                {
                    "url": "https://example.com/two",
                    "title": "Two",
                    "content": "Second snippet",
                },
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NIMBLE_API_KEY": "test-key"}):
            results = NimbleSearch("test query").search(max_results=2)

        # Verify the request shape: Bearer auth, correct endpoint, minimal
        # non-enterprise-safe payload (no include_answer / search_depth).
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://sdk.nimbleway.com/v1/search")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"], {"query": "test query", "max_results": 2})

        self.assertEqual(
            results,
            [
                {
                    "href": "https://example.com/one",
                    "body": "First snippet",
                    "title": "One",
                },
                {
                    "href": "https://example.com/two",
                    "body": "Second snippet",
                    "title": "Two",
                },
            ],
        )

    @patch("gpt_researcher.retrievers.nimble.nimble_search.requests.post")
    def test_search_falls_back_to_description_in_lite_mode(self, mock_post):
        # In the default (lite) depth, `content` is absent; `description`
        # carries the snippet text.
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/lite",
                    "title": "Lite",
                    "description": "Lite snippet",
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NIMBLE_API_KEY": "test-key"}):
            results = NimbleSearch("test query").search(max_results=1)

        self.assertEqual(
            results,
            [
                {
                    "href": "https://example.com/lite",
                    "body": "Lite snippet",
                    "title": "Lite",
                }
            ],
        )

    @patch("gpt_researcher.retrievers.nimble.nimble_search.requests.post")
    def test_search_returns_empty_on_no_results(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NIMBLE_API_KEY": "test-key"}):
            results = NimbleSearch("test query").search(max_results=5)

        self.assertEqual(results, [])

    @patch("gpt_researcher.retrievers.nimble.nimble_search.requests.post")
    def test_query_domains_passed_as_include_domains(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NIMBLE_API_KEY": "test-key"}):
            NimbleSearch("test query", query_domains=["example.com"]).search(
                max_results=3
            )

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["include_domains"], ["example.com"])


if __name__ == "__main__":
    unittest.main()
