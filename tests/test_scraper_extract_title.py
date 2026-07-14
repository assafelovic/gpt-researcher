"""Tests for scraper title extraction.

`extract_title` is annotated `-> str` and its result flows into image alt-text
and document metadata across every scraper backend. A `<title></title>` with no
text node made `soup.title.string` return `None`, breaking the string contract
and propagating `None` downstream.
"""

import unittest

from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import extract_title


def _title(html: str) -> str:
    return extract_title(BeautifulSoup(html, "html.parser"))


class TestExtractTitle(unittest.TestCase):
    def test_simple_title(self):
        self.assertEqual(_title("<title>Hello</title>"), "Hello")

    def test_empty_title_returns_empty_string_not_none(self):
        result = _title("<title></title>")
        self.assertIsNotNone(result)
        self.assertEqual(result, "")

    def test_no_title_tag(self):
        self.assertEqual(_title("<html><body>x</body></html>"), "")

    def test_title_is_whitespace_stripped(self):
        self.assertEqual(_title("<title>   spaced   </title>"), "spaced")

    def test_always_returns_str(self):
        for html in ("<title>Hello</title>", "<title></title>", "<html></html>"):
            self.assertIsInstance(_title(html), str)


if __name__ == "__main__":
    unittest.main()
