"""Regression test: GoogleSearch must URL-encode the query.

The Custom Search request URL was built by f-string interpolating the raw
query: ``...&q={search_query}&start=1``. Any reserved character in the
query corrupted the request:
  * ``&`` (e.g. "AT&T") injected a spurious query parameter,
  * ``#`` truncated everything after it (fragment),
  * spaces produced an invalid URL.

These tests pin proper percent-encoding by inspecting the URL handed to
``requests.get``.
"""

import os
import unittest
from unittest import mock
from urllib.parse import urlparse, parse_qs

from gpt_researcher.retrievers.google.google import GoogleSearch


class _Resp:
    status_code = 200
    text = '{"items": []}'


class GoogleSearchUrlEncodingTests(unittest.TestCase):
    def _search(self, query):
        env = {"GOOGLE_API_KEY": "k", "GOOGLE_CX_KEY": "c"}
        with mock.patch.dict(os.environ, env):
            gs = GoogleSearch(query)
        with mock.patch(
            "gpt_researcher.retrievers.google.google.requests.get",
            return_value=_Resp(),
        ) as m:
            gs.search()
        return m.call_args[0][0]  # the URL passed positionally

    def test_ampersand_in_query_is_encoded_not_split(self):
        url = self._search("AT&T market share")
        parsed = parse_qs(urlparse(url).query)
        # The whole query must survive as a single q param.
        self.assertEqual(parsed["q"], ["AT&T market share"])
        # No spurious top-level param leaked from the "&T".
        self.assertNotIn("T", parsed)

    def test_hash_in_query_is_not_treated_as_fragment(self):
        url = self._search("python #1 framework")
        self.assertEqual(urlparse(url).fragment, "")
        parsed = parse_qs(urlparse(url).query)
        self.assertEqual(parsed["q"], ["python #1 framework"])
        # start must still be present (the bug dropped it after the #).
        self.assertEqual(parsed["start"], ["1"])

    def test_spaces_are_encoded(self):
        url = self._search("hello world")
        self.assertNotIn(" ", url)
        parsed = parse_qs(urlparse(url).query)
        self.assertEqual(parsed["q"], ["hello world"])


if __name__ == "__main__":
    unittest.main()
