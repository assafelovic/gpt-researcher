"""Regression and unit tests for GroundRouteSearch query_domains, title handling, and max_results guards."""

import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.groundroute.groundroute import GroundRouteSearch


def _make_response(json_data, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


class TestGroundRouteQueryDomains(unittest.TestCase):
    @patch.dict("os.environ", {"GROUNDROUTE_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.groundroute.groundroute.requests.post")
    def test_groundroute_query_domains_applied(self, mock_post):
        mock_post.return_value = _make_response({"results": []})

        retriever = GroundRouteSearch(
            "python async",
            query_domains=["docs.python.org", "github.com"],
        )
        retriever.search()

        self.assertTrue(mock_post.called)
        sent_json = mock_post.call_args.kwargs.get("json")
        self.assertEqual(
            sent_json["query"],
            "(site:docs.python.org OR site:github.com) python async",
        )

    @patch.dict("os.environ", {"GROUNDROUTE_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.groundroute.groundroute.requests.post")
    def test_groundroute_query_domains_empty_or_none(self, mock_post):
        mock_post.return_value = _make_response({"results": []})

        retriever_empty = GroundRouteSearch("python async", query_domains=[])
        retriever_empty.search()
        sent_empty = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_empty["query"], "python async")

        retriever_none = GroundRouteSearch("python async", query_domains=None)
        retriever_none.search()
        sent_none = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_none["query"], "python async")

    @patch.dict("os.environ", {"GROUNDROUTE_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.groundroute.groundroute.requests.post")
    def test_groundroute_query_domains_filters_empty_whitespace(self, mock_post):
        mock_post.return_value = _make_response({"results": []})

        retriever = GroundRouteSearch(
            "python async",
            query_domains=["", "   ", "example.com"],
        )
        retriever.search()
        sent_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_json["query"], "(site:example.com) python async")

    @patch.dict("os.environ", {"GROUNDROUTE_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.groundroute.groundroute.requests.post")
    def test_groundroute_non_positive_max_results_returns_empty_without_request(
        self, mock_post
    ):
        retriever = GroundRouteSearch("python async")
        self.assertEqual(retriever.search(max_results=0), [])
        self.assertEqual(retriever.search(max_results=-5), [])
        mock_post.assert_not_called()

    @patch.dict("os.environ", {"GROUNDROUTE_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.groundroute.groundroute.requests.post")
    def test_groundroute_max_results_bounds_results(self, mock_post):
        mock_post.return_value = _make_response(
            {
                "results": [
                    {"url": f"https://example.com/{i}", "content": f"content {i}"}
                    for i in range(5)
                ]
            }
        )

        retriever = GroundRouteSearch("query")
        results = retriever.search(max_results=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["href"], "https://example.com/0")
        self.assertEqual(results[1]["href"], "https://example.com/1")

    @patch.dict("os.environ", {"GROUNDROUTE_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.groundroute.groundroute.requests.post")
    def test_groundroute_preserves_title_when_present(self, mock_post):
        mock_post.return_value = _make_response(
            {
                "results": [
                    {
                        "url": "https://example.com/doc",
                        "title": "Example Doc",
                        "content": "Doc content",
                    },
                    {
                        "url": "https://example.com/notitle",
                        "snippet": "No title snippet",
                    },
                ]
            }
        )

        retriever = GroundRouteSearch("query")
        results = retriever.search(max_results=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0],
            {
                "href": "https://example.com/doc",
                "body": "Doc content",
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
