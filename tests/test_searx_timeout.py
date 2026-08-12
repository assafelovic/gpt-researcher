import builtins
import importlib
import os
import typing
import unittest
from unittest.mock import Mock, patch


def _load_searx_class():
    with (
        patch.object(builtins, "Any", typing.Any, create=True),
        patch.object(builtins, "List", typing.List, create=True),
    ):
        module = importlib.import_module(
            "gpt_researcher.retrievers.searx.searx"
        )
    return module.SearxSearch


SearxSearch = _load_searx_class()


class SearxTimeoutTests(unittest.TestCase):
    def test_search_bounds_connect_and_read_time(self):
        response = Mock()
        response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "content": "result",
                }
            ]
        }

        with (
            patch.dict(os.environ, {"SEARX_URL": "https://search.example"}),
            patch(
                "gpt_researcher.retrievers.searx.searx.requests.get",
                return_value=response,
            ) as request,
        ):
            results = SearxSearch("query").search()

        self.assertEqual(
            results,
            [{"href": "https://example.com", "body": "result"}],
        )
        self.assertEqual(request.call_args.kwargs["timeout"], (5, 30))


if __name__ == "__main__":
    unittest.main()
