"""Regression tests for PDF URL detection in the BrowserScraper.

The scrape path used ``self.url.endswith(".pdf")``, which:
  * missed query strings / fragments (signed CDN/S3 links such as
    ``https://host/doc.pdf?sig=...`` are extremely common), and
  * was case-sensitive, so ``.PDF`` was not recognized.

These tests pin the corrected behavior via the ``_is_pdf_url`` helper.
"""

from gpt_researcher.scraper.browser.browser import _is_pdf_url


def test_plain_pdf_url_detected():
    assert _is_pdf_url("https://example.com/file.pdf") is True


def test_pdf_with_query_string_detected():
    # Signed CDN / S3 links carry the signature as a query string.
    assert _is_pdf_url("https://cdn.example.com/doc.pdf?sig=abc123&exp=999") is True


def test_pdf_with_fragment_detected():
    assert _is_pdf_url("https://example.com/doc.pdf#page=2") is True


def test_uppercase_extension_detected():
    assert _is_pdf_url("https://example.com/REPORT.PDF") is True


def test_non_pdf_url_not_detected():
    assert _is_pdf_url("https://example.com/article.html") is False


def test_pdf_substring_in_query_not_detected():
    # A ".pdf" appearing only in a query param must NOT trigger PDF handling.
    assert _is_pdf_url("https://example.com/view?file=report.pdf") is False


def test_empty_url_not_detected():
    assert _is_pdf_url("") is False
