"""Regression tests for XquikSearch null-field handling.

The Xquik API can return an explicit JSON ``null`` for ``tweets`` (no
results) or for a tweet's ``author`` / ``text`` fields. ``dict.get(key,
default)`` only substitutes the default when the key is *absent*, not when
its value is ``None`` — so ``tweet.get("author", {})`` returns ``None`` for
``{"author": null}``. The subsequent ``author.get("username")`` /
``text[:120]`` then raise, and the broad ``except`` in ``search()`` swallows
the error and silently drops *every* result.
"""

import io
import json
import os
import unittest
from unittest.mock import patch

from gpt_researcher.retrievers.xquik.xquik import XquikSearch


class TestXquikNullFields(unittest.TestCase):
    def setUp(self):
        os.environ["XQUIK_API_KEY"] = "test-key"

    def _run_with_payload(self, payload):
        raw = json.dumps(payload).encode("utf-8")

        class FakeResp:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *a):
                return False

            def read(self_inner):
                return raw

        with patch("urllib.request.urlopen", return_value=FakeResp()):
            return XquikSearch("test query").search(max_results=5)

    def test_null_author_still_returns_result(self):
        results = self._run_with_payload(
            {"tweets": [{"author": None, "text": "hello world", "id": "1"}]}
        )
        self.assertEqual(len(results), 1)
        self.assertIn("@unknown", results[0]["title"])
        self.assertIn("hello world", results[0]["body"])

    def test_null_text_and_id_do_not_crash(self):
        results = self._run_with_payload(
            {"tweets": [{"author": {"username": "bob"}, "text": None, "id": None}]}
        )
        self.assertEqual(len(results), 1)
        self.assertIn("@bob", results[0]["title"])

    def test_null_tweets_returns_empty_list(self):
        results = self._run_with_payload({"tweets": None})
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
