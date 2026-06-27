import os
import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.caesar.caesar import CaesarSearch


class TestCaesarSearch(unittest.TestCase):
    def test_works_without_api_key(self):
        # Caesar is keyless: constructing with no env key must not raise and
        # must not attach an Authorization header.
        with patch.dict(os.environ, {}, clear=True):
            retriever = CaesarSearch("test query")
        self.assertEqual(retriever.api_key, "")
        self.assertNotIn("Authorization", retriever.headers)

    def test_api_key_adds_bearer_header(self):
        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
            retriever = CaesarSearch("test query")
        self.assertEqual(retriever.headers.get("Authorization"), "Bearer sk_live_test")

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_search_normalizes_results(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com/one",
                    "title": "One",
                    "snippet": "First snippet",
                    "score": 0.91,
                },
                {
                    "url": "https://example.com/two",
                    "title": "Two",
                    "snippet": "Second snippet",
                    "score": 0.84,
                },
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            results = CaesarSearch("test query").search(max_results=2)

        called_url = mock_post.call_args.args[0]
        self.assertEqual(called_url, "https://alpha.api.trycaesar.com/v1/search")
        self.assertEqual(
            results,
            [
                {"href": "https://example.com/one", "body": "First snippet"},
                {"href": "https://example.com/two", "body": "Second snippet"},
            ],
        )

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_search_falls_back_across_field_names(self, mock_post):
        # url may arrive as canonical_url/source_url; snippet as content/passage.
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"canonical_url": "https://example.com/c", "content": "body via content"},
                {"source_url": "https://example.com/s", "passage": "body via passage"},
                {"title": "no url, dropped"},
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            results = CaesarSearch("test query").search(max_results=5)

        self.assertEqual(
            results,
            [
                {"href": "https://example.com/c", "body": "body via content"},
                {"href": "https://example.com/s", "body": "body via passage"},
            ],
        )

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_search_returns_empty_on_error(self, mock_post):
        mock_post.side_effect = Exception("network down")
        with patch.dict(os.environ, {}, clear=True):
            results = CaesarSearch("test query").search()
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
