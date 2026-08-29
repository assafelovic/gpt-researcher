import os
import unittest
from unittest.mock import MagicMock, patch

import requests

from gpt_researcher.retrievers.webiq.webiq import WebIQSearch


class TestWebIQSearch(unittest.TestCase):
    def test_missing_api_key_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "WEBIQ_API_KEY"):
                WebIQSearch("test query")

    def test_header_api_key_takes_precedence(self):
        with patch.dict(os.environ, {"WEBIQ_API_KEY": "environment-key"}, clear=True):
            retriever = WebIQSearch(
                "test query", headers={"webiq_api_key": "header-key"}
            )
        self.assertEqual(retriever.api_key, "header-key")

    def test_domains_use_or_and_invalid_values_are_dropped(self):
        with patch.dict(os.environ, {"WEBIQ_API_KEY": "test-key"}, clear=True):
            query = WebIQSearch(
                "test query",
                query_domains=[
                    "https://one.example/path",
                    "two.example",
                    "bad domain.example",
                    "two.example",
                ],
            )._build_query()
        self.assertEqual(query, "test query (site:one.example OR site:two.example)")

    def test_string_domain_is_treated_as_one_filter(self):
        with patch.dict(os.environ, {"WEBIQ_API_KEY": "test-key"}, clear=True):
            query = WebIQSearch(
                "test query", query_domains="example.com"
            )._build_query()
        self.assertEqual(query, "test query site:example.com")

    def test_many_domains_preserve_the_complete_research_query(self):
        long_query = (
            "what are the latest breakthroughs in solid state battery "
            "manufacturing and commercialization " * 4
        ).strip()
        domains = [f"subdomain-{i}.example.com" for i in range(40)]
        with patch.dict(os.environ, {"WEBIQ_API_KEY": "test-key"}, clear=True):
            query = WebIQSearch(long_query, query_domains=domains)._build_query()

        self.assertLessEqual(len(query), WebIQSearch.MAX_QUERY_LENGTH)
        self.assertTrue(query.startswith(long_query))
        self.assertLess(query.count("site:"), len(domains))
        self.assertTrue(query.endswith(")"))

    def test_all_invalid_domains_emit_warning(self):
        with patch.dict(os.environ, {"WEBIQ_API_KEY": "test-key"}, clear=True):
            with self.assertLogs(
                "gpt_researcher.retrievers.webiq.webiq", level="WARNING"
            ):
                query = WebIQSearch(
                    "test query", query_domains=["bad domain", "bad)domain"]
                )._build_query()
        self.assertEqual(query, "test query")

    def test_invalid_content_and_safe_search_values_warn_and_fall_back(self):
        env = {
            "WEBIQ_API_KEY": "test-key",
            "WEBIQ_CONTENT_FORMAT": "unknown",
            "WEBIQ_SAFE_SEARCH": "moderate",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertLogs(
                "gpt_researcher.retrievers.webiq.webiq", level="WARNING"
            ):
                retriever = WebIQSearch("test query")
        self.assertEqual(retriever.content_format, "passage")
        self.assertEqual(retriever.safe_search, "strict")

    @patch("gpt_researcher.retrievers.webiq.webiq.requests.post")
    def test_search_uses_custom_endpoint_without_manual_host(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"webResults": []}
        mock_post.return_value = response
        env = {
            "WEBIQ_API_KEY": "test-key",
            "WEBIQ_ENDPOINT": "https://proxy.example/v3/search/web",
            "WEBIQ_TIMEOUT": "20",
        }
        with patch.dict(os.environ, env, clear=True):
            WebIQSearch("test query").search(max_results=3)

        call = mock_post.call_args
        self.assertEqual(call.args[0], "https://proxy.example/v3/search/web")
        self.assertNotIn("host", call.kwargs["headers"])
        self.assertEqual(call.kwargs["timeout"], 20)
        self.assertEqual(call.kwargs["json"]["maxLength"], 2500)

    @patch("gpt_researcher.retrievers.webiq.webiq.requests.post")
    def test_search_normalizes_and_guards_malformed_fields(self, mock_post):
        response = MagicMock()
        response.json.return_value = {
            "webResults": [
                {
                    "title": "Example",
                    "url": "https://example.com/article",
                    "content": "Relevant passage.",
                },
                {
                    "title": {"unexpected": "object"},
                    "url": "https://example.com/malformed",
                    "content": ["unexpected", "list"],
                },
                {"title": "Invalid URL", "url": {"not": "a string"}},
                None,
            ]
        }
        mock_post.return_value = response

        with patch.dict(os.environ, {"WEBIQ_API_KEY": "test-key"}, clear=True):
            results = WebIQSearch("test query").search(max_results=5)

        self.assertEqual(
            results,
            [
                {
                    "title": "Example",
                    "href": "https://example.com/article",
                    "body": "Relevant passage.",
                },
                {
                    "title": "",
                    "href": "https://example.com/malformed",
                    "body": "",
                },
            ],
        )

    @patch("gpt_researcher.retrievers.webiq.webiq.requests.post")
    def test_request_failure_returns_empty_list(self, mock_post):
        mock_post.side_effect = requests.Timeout("timed out")
        with patch.dict(os.environ, {"WEBIQ_API_KEY": "test-key"}, clear=True):
            self.assertEqual(WebIQSearch("test query").search(), [])

    @patch("gpt_researcher.retrievers.webiq.webiq.requests.post")
    def test_malformed_response_returns_empty_list(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"webResults": None}
        mock_post.return_value = response
        with patch.dict(os.environ, {"WEBIQ_API_KEY": "test-key"}, clear=True):
            self.assertEqual(WebIQSearch("test query").search(), [])

    def test_declares_that_results_still_need_scraping(self):
        # The "content" field is a snippet sized by WEBIQ_MAX_LENGTH, not the
        # page, so the URL must still be fetched. Without this declaration the
        # legacy >100-character heuristic would treat it as fetched content.
        self.assertIs(WebIQSearch.requires_scraping, True)


if __name__ == "__main__":
    unittest.main()
