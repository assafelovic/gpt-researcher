import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.crw.crw import CRWRetriever


def make_response(json_data, status_code=200):
    """Build a fake requests.Response-like object."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


class CRWRetrieverTests(unittest.TestCase):
    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_search_returns_href_body_shape(self, mock_post):
        mock_post.return_value = make_response(
            {
                "success": True,
                "data": [
                    {
                        "url": "https://example.com/one",
                        "description": "desc one",
                        "markdown": "markdown one",
                    }
                ],
            }
        )

        retriever = CRWRetriever("rust async runtimes")
        results = retriever.search()

        self.assertEqual(
            results,
            [{"href": "https://example.com/one", "body": "markdown one"}],
        )

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_markdown_preferred_over_description(self, mock_post):
        mock_post.return_value = make_response(
            {
                "success": True,
                "data": [
                    {
                        "url": "https://example.com/md",
                        "description": "fallback description",
                        "markdown": "rich markdown",
                    },
                    {
                        "url": "https://example.com/no-md",
                        "description": "only description",
                    },
                ],
            }
        )

        retriever = CRWRetriever("query")
        results = retriever.search()

        self.assertEqual(results[0]["body"], "rich markdown")
        self.assertEqual(results[1]["body"], "only description")

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_empty_data_returns_empty_list(self, mock_post):
        mock_post.return_value = make_response({"success": True, "data": []})

        retriever = CRWRetriever("query")
        results = retriever.search()

        self.assertEqual(results, [])

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key_does_not_raise(self):
        # Constructing without CRW_API_KEY must not raise; key falls back to blank.
        retriever = CRWRetriever("query")
        self.assertEqual(retriever.api_key, "")
        # No Authorization header is added when the key is blank (self-host case).
        self.assertNotIn("Authorization", retriever.headers)

    @patch.dict(
        "os.environ",
        {"CRW_API_KEY": "test-key", "CRW_API_URL": "http://localhost:3000/"},
        clear=False,
    )
    def test_base_url_override_strips_trailing_slash(self):
        retriever = CRWRetriever("query")
        self.assertEqual(retriever.base_url, "http://localhost:3000")

    @patch.dict("os.environ", {"CRW_API_KEY": "test-key"}, clear=False)
    @patch("gpt_researcher.retrievers.crw.crw.requests.post")
    def test_envelope_failure_returns_empty_list(self, mock_post):
        mock_post.return_value = make_response(
            {"success": False, "error": "rate limited"}
        )

        retriever = CRWRetriever("query")
        results = retriever.search()

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
