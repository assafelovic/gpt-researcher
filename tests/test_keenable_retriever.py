import os
import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.keenable.keenable import MAX_BODY_CHARS, KeenableSearch


class TestKeenableSearch(unittest.TestCase):
    def test_missing_api_key_uses_the_keyless_endpoint(self):
        # Unlike the other retrievers here, Keenable does not require a key.
        with patch.dict(os.environ, {}, clear=True):
            retriever = KeenableSearch("test query")
        self.assertEqual(retriever.api_key, "")

    @patch("gpt_researcher.retrievers.keenable.keenable.requests.post")
    def test_search_normalizes_results(self, mock_post):
        # The API returns both fields on every result: `description` is
        # frequently empty and `snippet` carries the page text.
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/one",
                    "title": "One",
                    "description": "",
                    "snippet": "First page text",
                },
                {
                    "url": "https://example.com/two",
                    "title": "Two",
                    "description": "",
                    "snippet": "Second page text",
                },
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            results = KeenableSearch("test query").search(max_results=2)

        self.assertEqual(
            results,
            [
                {
                    "href": "https://example.com/one",
                    "title": "One",
                    "body": "First page text",
                },
                {
                    "href": "https://example.com/two",
                    "title": "Two",
                    "body": "Second page text",
                },
            ],
        )

    @patch("gpt_researcher.retrievers.keenable.keenable.requests.post")
    def test_search_falls_back_to_description(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/one",
                    "title": "One",
                    "description": "A description",
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            results = KeenableSearch("test query").search()

        self.assertEqual(results[0]["body"], "A description")

    @patch("gpt_researcher.retrievers.keenable.keenable.requests.post")
    def test_search_collapses_whitespace_and_caps_the_body(self, mock_post):
        # Snippets arrive as raw page text, newlines included, and run far
        # longer than the snippet the other retrievers return.
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/one",
                    "title": "One",
                    "description": "",
                    "snippet": "line one\n\nline two" + " padding" * 500,
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            body = KeenableSearch("test query").search()[0]["body"]

        self.assertEqual(len(body), MAX_BODY_CHARS)
        self.assertNotIn("\n", body)
        self.assertTrue(body.startswith("line one line two"))

    @patch("gpt_researcher.retrievers.keenable.keenable.requests.post")
    def test_search_drops_results_without_a_url(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"title": "No URL", "snippet": "text"},
                {"url": "https://example.com/one", "title": "One", "snippet": "text"},
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            results = KeenableSearch("test query").search()

        self.assertEqual([r["href"] for r in results], ["https://example.com/one"])


if __name__ == "__main__":
    unittest.main()
