"""Regression tests for SearchApiSearch missing-key handling.

``SearchApiSearch.search`` used to index the JSON response directly:
``search_results["organic_results"]`` and ``result["link"]`` /
``result["title"]`` / ``result["snippet"]``. Any absent key raised
``KeyError``, which the broad ``except Exception`` swallowed -- silently
turning a partially-shaped response into an *empty* result list and
dropping every source.

These tests mock the HTTP layer and assert that:
  * a response with no ``organic_results`` key yields [] without raising,
  * results missing individual fields still produce entries (with empty
    strings) instead of being dropped wholesale.
"""

import os
import unittest
from unittest.mock import patch

from gpt_researcher.retrievers.searchapi.searchapi import SearchApiSearch


class _FakeResp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class TestSearchApiMissingKeys(unittest.TestCase):
    def setUp(self):
        os.environ["SEARCHAPI_API_KEY"] = "test-key"

    def _search(self, payload):
        with patch("requests.get", return_value=_FakeResp(payload)):
            return SearchApiSearch("q").search(max_results=5)

    def test_missing_organic_results_returns_empty(self):
        # Previously raised KeyError -> swallowed -> [] anyway, but via an
        # error path; now it is a clean, intentional empty result.
        self.assertEqual(self._search({"error": "quota exceeded"}), [])

    def test_result_missing_fields_is_not_dropped(self):
        results = self._search(
            {"organic_results": [{"link": "https://example.com/a"}]}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["href"], "https://example.com/a")
        self.assertEqual(results[0]["title"], "")
        self.assertEqual(results[0]["body"], "")

    def test_result_missing_link_still_processed(self):
        results = self._search(
            {"organic_results": [{"title": "t", "snippet": "s"}]}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["href"], "")
        self.assertEqual(results[0]["title"], "t")

    def test_null_payload_returns_empty(self):
        self.assertEqual(self._search(None), [])


if __name__ == "__main__":
    unittest.main()
