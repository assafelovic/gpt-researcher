"""Regression tests for PDF detection in Scraper.get_scraper.

PDF links were detected with ``link.endswith(".pdf")``, which:
  * missed query strings / fragments (signed CDN/S3 links such as
    ``https://host/doc.pdf?sig=...`` are extremely common), and
  * was case-sensitive, so ``.PDF`` was not recognized.

In both cases a real PDF was routed to the configured HTML scraper
(e.g. BeautifulSoup) instead of PyMuPDFScraper, producing garbage or
empty content. These tests pin correct routing.
"""

import unittest

from gpt_researcher.scraper.scraper import Scraper
from gpt_researcher.scraper import PyMuPDFScraper, BeautifulSoupScraper


def _scraper():
    # worker_pool is unused by get_scraper; default scraper is "bs".
    return Scraper(urls=["https://example.com"], user_agent="ua", scraper="bs", worker_pool=None)


class GetScraperPdfDetectionTests(unittest.TestCase):
    def test_plain_pdf_url_uses_pymupdf(self):
        s = _scraper()
        self.assertIs(s.get_scraper("https://example.com/doc.pdf"), PyMuPDFScraper)

    def test_pdf_with_query_string_uses_pymupdf(self):
        s = _scraper()
        self.assertIs(
            s.get_scraper("https://example.com/doc.pdf?sig=abc123&exp=999"),
            PyMuPDFScraper,
        )

    def test_pdf_with_fragment_uses_pymupdf(self):
        s = _scraper()
        self.assertIs(s.get_scraper("https://example.com/doc.pdf#page=2"), PyMuPDFScraper)

    def test_uppercase_pdf_extension_uses_pymupdf(self):
        s = _scraper()
        self.assertIs(s.get_scraper("https://example.com/REPORT.PDF"), PyMuPDFScraper)

    def test_non_pdf_url_uses_default_scraper(self):
        s = _scraper()
        self.assertIs(s.get_scraper("https://example.com/article"), BeautifulSoupScraper)

    def test_pdf_substring_in_query_is_not_treated_as_pdf(self):
        # "pdf" only in the query, not the path extension -> NOT a pdf.
        s = _scraper()
        self.assertIs(
            s.get_scraper("https://example.com/article?format=pdf"),
            BeautifulSoupScraper,
        )


if __name__ == "__main__":
    unittest.main()
