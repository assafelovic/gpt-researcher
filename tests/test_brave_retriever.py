import os
import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.brave.brave import BraveSearch


class TestBraveSearch(unittest.TestCase):
    def test_missing_api_key_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(Exception, "BRAVE_API_KEY"):
                BraveSearch("test query")

    @patch("gpt_researcher.retrievers.brave.brave.requests.get")
    def test_search_normalizes_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "url": "https://example.com/one",
                        "title": "One",
                        "description": "First snippet",
                    },
                    {
                        "url": "https://example.com/two",
                        "title": "Two",
                        "description": "Second snippet",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key"}):
            results = BraveSearch("test query").search(max_results=2)

        mock_get.assert_called_once_with(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "X-Subscription-Token": "test-key",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
            },
            params={"q": "test query", "count": 2},
            timeout=20,
        )
        self.assertEqual(
            results,
            [
                {
                    "href": "https://example.com/one",
                    "title": "One",
                    "body": "First snippet",
                },
                {
                    "href": "https://example.com/two",
                    "title": "Two",
                    "body": "Second snippet",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
