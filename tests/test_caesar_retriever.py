import json
import os
import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.caesar.caesar import CaesarSearch


class TestCaesarSearch(unittest.TestCase):
    def test_missing_api_key_raises(self):
        # Caesar requires an API key: constructing with no env key must raise.
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception):
                CaesarSearch("test query")

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

        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
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

        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
            results = CaesarSearch("test query").search(max_results=5)

        self.assertEqual(
            results,
            [
                {"href": "https://example.com/c", "body": "body via content"},
                {"href": "https://example.com/s", "body": "body via passage"},
            ],
        )

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_search_prefers_query_selected_passages(self, mock_post):
        # `snippet` is the page's meta description, identical for every query that
        # surfaces the document. `passages` are selected for this query.
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://tokio.rs/blog/2019-10-scheduler",
                    "snippet": "A blog about the Tokio runtime.",
                    "passages": [
                        {"text": "Work stealing balances load across worker threads."},
                        {"text": "The new scheduler avoids the atomic increment in wake_by_ref."},
                    ],
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
            results = CaesarSearch("work stealing").search(max_results=1)

        self.assertEqual(
            results[0]["body"],
            "Work stealing balances load across worker threads.\n\n"
            "The new scheduler avoids the atomic increment in wake_by_ref.",
        )

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_search_ignores_blank_passages(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"url": "https://example.com/a", "snippet": "fallback", "passages": [{"text": "  "}]}
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
            results = CaesarSearch("q").search(max_results=1)

        self.assertEqual(results[0]["body"], "fallback")

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_query_domains_scope_the_search(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"url": "https://tokio.rs/x", "snippet": "s"}]}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
            CaesarSearch("q", query_domains=["tokio.rs"]).search(max_results=1)

        body = json.loads(mock_post.call_args.kwargs["data"])
        self.assertEqual(body["source_policy"], {"include_domains": ["tokio.rs"]})

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_no_source_policy_without_query_domains(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"url": "https://example.com/a", "snippet": "s"}]}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
            CaesarSearch("q").search(max_results=1)

        body = json.loads(mock_post.call_args.kwargs["data"])
        self.assertNotIn("source_policy", body)

    @patch("gpt_researcher.retrievers.caesar.caesar.requests.post")
    def test_search_returns_empty_on_error(self, mock_post):
        mock_post.side_effect = Exception("network down")
        with patch.dict(os.environ, {"CAESAR_API_KEY": "sk_live_test"}, clear=True):
            results = CaesarSearch("test query").search()
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
