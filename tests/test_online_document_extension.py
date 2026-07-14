"""Regression test for OnlineDocumentLoader._get_extension case handling."""

from gpt_researcher.document.online_document import OnlineDocumentLoader


def test_get_extension_lowercases_uppercase_suffix():
    # Loader dict keys are lower-case ("pdf", "docx"); an upper-case URL
    # extension must be normalised so the right loader is selected instead
    # of silently falling through to the unsupported branch.
    assert OnlineDocumentLoader._get_extension("https://x.com/report.PDF") == ".pdf"
    assert OnlineDocumentLoader._get_extension("https://x.com/doc.DOCX") == ".docx"


def test_get_extension_strips_query_string():
    # Signed CDN/S3 URLs carry a query string after the real extension.
    assert (
        OnlineDocumentLoader._get_extension("https://x.com/report.PDF?sig=abc&t=1")
        == ".pdf"
    )
    assert OnlineDocumentLoader._get_extension("https://x.com/a.pdf") == ".pdf"


def test_get_extension_no_extension():
    assert OnlineDocumentLoader._get_extension("https://x.com/page") == ""
