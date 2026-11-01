"""Regression test for OnlineDocumentLoader._get_extension case handling."""

import asyncio

import pytest

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


@pytest.mark.parametrize(
    ("url", "extension"),
    [
        ("https://example.com/report.PDF#page=2", ".pdf"),
        ("https://example.com/notes.txt#section", ".txt"),
        ("https://example.com/report.pdf#section?download=1", ".pdf"),
        ("https://example.com/report.PDF?signature=abc#page=2", ".pdf"),
        ("https://example.com/page#attachment.pdf", ""),
        ("https://example.com", ""),
        ("https://example.com/#attachment.pdf", ""),
    ],
)
def test_get_extension_uses_only_url_path(url, extension):
    assert OnlineDocumentLoader._get_extension(url) == extension


@pytest.mark.parametrize("fragment", ["", "#section", "#section?download=1"])
def test_text_document_with_fragment_is_loaded_and_cleaned_up(tmp_path, fragment):
    loader = OnlineDocumentLoader([])
    extension = loader._get_extension("https://example.com/notes.txt" + fragment)
    path = tmp_path / ("download" + extension)
    path.write_text("Research evidence", encoding="utf-8")

    pages = asyncio.run(loader._load_document(str(path), extension.lstrip(".")))

    assert [page.page_content for page in pages] == ["Research evidence"]
    assert not path.exists()
