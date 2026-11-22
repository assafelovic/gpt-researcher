"""Regression and unit tests for CRWRetriever query_domains, title handling, and max_results guards."""

import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.crw.crw import CRWRetriever


def _make_response(json_data, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


class TestCRWQueryDomains(unittest.TestCase):
    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_crw_query_domains_applied(self, mock_post):
        mock_post.return_value = _make_response({"success": True, "data": []})

        retriever = CRWRetriever(
            "python async",
            query_domains=["docs.python.org", "github.com"],
        )
        retriever.search()

        self.assertTrue(mock_post.called)
        sent_body = mock_post.call_args.kwargs.get("data")
        import json

        payload = json.loads(sent_body)
        self.assertEqual(
            payload["query"],
            "(site:docs.python.org OR site:github.com) python async",
        )

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_crw_query_domains_empty_or_none(self, mock_post):
        mock_post.return_value = _make_response({"success": True, "data": []})

        import json

        retriever_empty = CRWRetriever("python async", query_domains=[])
        retriever_empty.search()
        payload_empty = json.loads(mock_post.call_args.kwargs["data"])
        self.assertEqual(payload_empty["query"], "python async")

        retriever_none = CRWRetriever("python async", query_domains=None)
        retriever_none.search()
        payload_none = json.loads(mock_post.call_args.kwargs["data"])
        self.assertEqual(payload_none["query"], "python async")

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_crw_query_domains_filters_empty_whitespace(self, mock_post):
        mock_post.return_value = _make_response({"success": True, "data": []})

        import json

        retriever = CRWRetriever(
            "python async",
            query_domains=["", "   ", "example.com"],
        )
        retriever.search()
        payload = json.loads(mock_post.call_args.kwargs["data"])
        self.assertEqual(payload["query"], "(site:example.com) python async")

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_crw_non_positive_max_results_returns_empty_without_request(
        self, mock_post
    ):
        retriever = CRWRetriever("python async")
        self.assertEqual(retriever.search(max_results=0), [])
        self.assertEqual(retriever.search(max_results=-5), [])
        mock_post.assert_not_called()

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_crw_internal_search_non_positive_limit(self, mock_post):
        retriever = CRWRetriever("python async")
        res_zero = retriever._search("python async", max_results=0)
        self.assertEqual(res_zero, {"success": True, "data": []})
        res_neg = retriever._search("python async", max_results=-3)
        self.assertEqual(res_neg, {"success": True, "data": []})
        mock_post.assert_not_called()

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_crw_max_results_bounds_results(self, mock_post):
        mock_post.return_value = _make_response(
            {
                "success": True,
                "data": [
                    {"url": f"https://example.com/{i}", "description": f"desc {i}"}
                    for i in range(5)
                ],
            }
        )

        retriever = CRWRetriever("query")
        results = retriever.search(max_results=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["href"], "https://example.com/0")
        self.assertEqual(results[1]["href"], "https://example.com/1")

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_crw_preserves_title_when_present(self, mock_post):
        mock_post.return_value = _make_response(
            {
                "success": True,
                "data": [
                    {
                        "url": "https://example.com/doc",
                        "title": "Example Doc",
                        "markdown": "Doc markdown",
                    },
                    {
                        "url": "https://example.com/notitle",
                        "description": "No title snippet",
                    },
                ],
            }
        )

        retriever = CRWRetriever("query")
        results = retriever.search(max_results=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0],
            {
                "href": "https://example.com/doc",
                "body": "Doc markdown",
                "title": "Example Doc",
            },
        )
        self.assertEqual(
            results[1],
            {
                "href": "https://example.com/notitle",
                "body": "No title snippet",
            },
        )


if __name__ == "__main__":
    unittest.main()
