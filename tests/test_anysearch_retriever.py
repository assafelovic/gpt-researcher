"""Tests for the AnySearch retriever.

Covers: query/param mapping, anonymous vs keyed auth headers, empty-result
vs error distinction, and the main error branches. All HTTP is mocked;
no real network calls are made here.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.anysearch.anysearch import (
    ANYSEARCH_API_URL,
    ANYSEARCH_CLIENT_ID,
    AnySearchRetriever,
)


def _ok_response(results, request_id="req-test-123", code=0):
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "code": code,
        "message": "ok" if code == 0 else "boom",
        "request_id": request_id,
        "data": {"results": results},
    }
    return response


def _clean_env():
    return patch.dict(os.environ, {}, clear=True)


class TestAnySearchRetriever(unittest.TestCase):
    # -- auth header behavior -------------------------------------------

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_anonymous_sends_no_authorization_header(self, mock_post):
        mock_post.return_value = _ok_response([])
        with _clean_env():
            AnySearchRetriever("test query").search(max_results=3)
        _, kwargs = mock_post.call_args
        self.assertNotIn("Authorization", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["X-Anysearch-Client"],
                         ANYSEARCH_CLIENT_ID)

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_keyed_sends_bearer_header(self, mock_post):
        mock_post.return_value = _ok_response([])
        with patch.dict(os.environ, {"ANYSEARCH_API_KEY": "secret-key"}):
            AnySearchRetriever("test query").search(max_results=3)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret-key")

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_blank_key_is_treated_as_anonymous(self, mock_post):
        mock_post.return_value = _ok_response([])
        with patch.dict(os.environ, {"ANYSEARCH_API_KEY": "   "}):
            AnySearchRetriever("test query").search(max_results=3)
        _, kwargs = mock_post.call_args
        self.assertNotIn("Authorization", kwargs["headers"])

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_header_key_overrides_env(self, mock_post):
        mock_post.return_value = _ok_response([])
        with patch.dict(os.environ, {"ANYSEARCH_API_KEY": "env-key"}):
            AnySearchRetriever(
                "test query", headers={"anysearch_api_key": "header-key"}
            ).search()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer header-key")

    # -- query / param mapping ----------------------------------------

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_payload_mapping_and_clamping(self, mock_post):
        mock_post.return_value = _ok_response([])
        with _clean_env():
            AnySearchRetriever("hello world").search(max_results=50)
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], ANYSEARCH_API_URL)
        self.assertEqual(kwargs["json"],
                         {"query": "hello world", "max_results": 10})
        self.assertNotIn("tag", kwargs["json"])
        self.assertNotIn("params", kwargs["json"])

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_max_results_floor(self, mock_post):
        mock_post.return_value = _ok_response([])
        with _clean_env():
            AnySearchRetriever("q").search(max_results=0)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["max_results"], 1)

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_tag_and_params_passed_through(self, mock_post):
        mock_post.return_value = _ok_response([])
        with _clean_env():
            AnySearchRetriever("react hooks", tag="code.doc",
                               params={"library": "react"}).search()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["tag"], "code.doc")
        self.assertEqual(kwargs["json"]["params"], {"library": "react"})

    # -- result normalization ------------------------------------------

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_results_normalized(self, mock_post):
        mock_post.return_value = _ok_response([
            {"title": "One", "url": "https://example.com/1",
             "content": "First content"},
            {"title": "Two", "url": "https://example.com/2",
             "snippet": "Second snippet"},
            {"title": "No URL", "content": "skipped"},
            "not-a-dict",
        ])
        with _clean_env():
            retriever = AnySearchRetriever("q")
            results = retriever.search()
        self.assertEqual(results, [
            {"href": "https://example.com/1", "title": "One",
             "body": "First content"},
            {"href": "https://example.com/2", "title": "Two",
             "body": "Second snippet"},
        ])
        self.assertEqual(retriever.last_request_id, "req-test-123")
        self.assertIsNone(retriever.last_error)

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_empty_results_are_not_an_error(self, mock_post):
        mock_post.return_value = _ok_response([])
        with _clean_env():
            retriever = AnySearchRetriever("q")
            results = retriever.search()
        self.assertEqual(results, [])
        self.assertIsNone(retriever.last_error)

    # -- error branches -------------------------------------------------

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_business_code_error_is_not_empty_results(self, mock_post):
        mock_post.return_value = _ok_response([], code=4003)
        with _clean_env():
            retriever = AnySearchRetriever("q")
            results = retriever.search()
        self.assertEqual(results, [])
        self.assertIsNotNone(retriever.last_error)
        self.assertIn("4003", retriever.last_error)

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_http_401_records_auth_error(self, mock_post):
        response = MagicMock()
        response.ok = False
        response.status_code = 401
        mock_post.return_value = response
        with _clean_env():
            retriever = AnySearchRetriever("q")
            results = retriever.search()
        self.assertEqual(results, [])
        self.assertIn("authentication failed", retriever.last_error.lower())

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_http_429_records_rate_limit(self, mock_post):
        response = MagicMock()
        response.ok = False
        response.status_code = 429
        mock_post.return_value = response
        with _clean_env():
            retriever = AnySearchRetriever("q")
            results = retriever.search()
        self.assertEqual(results, [])
        self.assertIn("rate limit", retriever.last_error.lower())

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_timeout_records_error(self, mock_post):
        import requests as req_mod
        mock_post.side_effect = req_mod.Timeout("timed out")
        with _clean_env():
            retriever = AnySearchRetriever("q")
            results = retriever.search()
        self.assertEqual(results, [])
        self.assertIn("timed out", retriever.last_error.lower())

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_non_json_response_records_error(self, mock_post):
        response = MagicMock()
        response.ok = True
        response.status_code = 200
        response.json.side_effect = ValueError("no json")
        mock_post.return_value = response
        with _clean_env():
            retriever = AnySearchRetriever("q")
            results = retriever.search()
        self.assertEqual(results, [])
        self.assertIsNotNone(retriever.last_error)

    @patch("gpt_researcher.retrievers.anysearch.anysearch.requests.post")
    def test_no_key_in_logs_or_snapshots(self, mock_post):
        mock_post.return_value = _ok_response([], code=5001)
        with patch.dict(os.environ, {"ANYSEARCH_API_KEY": "super-secret"}):
            retriever = AnySearchRetriever("q")
            retriever.search()
        self.assertNotIn("super-secret", retriever.last_error or "")

    # -- registration ---------------------------------------------------

    def test_registered_under_anysearch_name(self):
        from gpt_researcher.actions.retriever import get_retriever
        self.assertIs(get_retriever("anysearch"), AnySearchRetriever)

    def test_name_passes_config_validation(self):
        from gpt_researcher.retrievers.utils import get_all_retriever_names
        self.assertIn("anysearch", get_all_retriever_names())


if __name__ == "__main__":
    unittest.main()
