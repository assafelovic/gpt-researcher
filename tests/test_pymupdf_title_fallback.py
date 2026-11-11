"""Unit tests for PyMuPDFScraper title extraction and fallback."""

from unittest.mock import MagicMock, patch

from gpt_researcher.scraper.pymupdf.pymupdf import PyMuPDFScraper, _fallback_title


class _FakePage:
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata


def test_fallback_title_from_url_with_dashes_and_underscores():
    url = "https://susproc.jrc.ec.europa.eu/product-bureau/sites/default/files/2021-01/UM3_Indicator_6.1_v1.1_21pp.pdf"
    assert _fallback_title(url) == "UM3 Indicator 6.1 v1.1 21pp"


def test_fallback_title_from_url_with_urlencoded_characters():
    url = "https://example.com/docs/Annual%20Report_2025-Q3.pdf?download=true"
    assert _fallback_title(url) == "Annual Report 2025 Q3"


def test_fallback_title_from_local_path():
    path = "/home/user/downloads/my-research_paper.pdf"
    assert _fallback_title(path) == "my research paper"


def test_fallback_title_root_url_fallback():
    url = "https://example.com/"
    assert _fallback_title(url) == "example.com"


def test_pymupdf_scraper_preserves_metadata_title():
    scraper = PyMuPDFScraper("https://example.com/sample.pdf")
    fake_doc = [_FakePage("Page 1 content", {"title": "  Deep Research with Agents  "})]

    with patch("gpt_researcher.scraper.pymupdf.pymupdf.PyMuPDFLoader") as mock_loader, \
         patch("gpt_researcher.scraper.pymupdf.pymupdf.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"%PDF-1.4"]
        mock_get.return_value = mock_resp
        mock_loader.return_value.load.return_value = fake_doc

        content, images, title = scraper.scrape()

    assert content == "Page 1 content"
    assert images == []
    assert title == "Deep Research with Agents"


def test_pymupdf_scraper_falls_back_when_metadata_title_missing():
    scraper = PyMuPDFScraper("https://example.com/reports/RMI_Document_Repository_Public-Reports_2024.pdf")
    fake_doc = [_FakePage("Page 1 content", {})]

    with patch("gpt_researcher.scraper.pymupdf.pymupdf.PyMuPDFLoader") as mock_loader, \
         patch("gpt_researcher.scraper.pymupdf.pymupdf.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"%PDF-1.4"]
        mock_get.return_value = mock_resp
        mock_loader.return_value.load.return_value = fake_doc

        _content, _images, title = scraper.scrape()

    assert title == "RMI Document Repository Public Reports 2024"


def test_pymupdf_scraper_falls_back_when_metadata_title_is_empty_or_whitespace():
    scraper = PyMuPDFScraper("https://example.com/reports/RMI_Document_Repository_Public-Reports_2024.pdf")
    fake_doc = [_FakePage("Page 1 content", {"title": "   "})]

    with patch("gpt_researcher.scraper.pymupdf.pymupdf.PyMuPDFLoader") as mock_loader, \
         patch("gpt_researcher.scraper.pymupdf.pymupdf.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"%PDF-1.4"]
        mock_get.return_value = mock_resp
        mock_loader.return_value.load.return_value = fake_doc

        _content, _images, title = scraper.scrape()

    assert title == "RMI Document Repository Public Reports 2024"


def test_pymupdf_scraper_empty_doc_returns_empty_title():
    scraper = PyMuPDFScraper("https://example.com/empty.pdf")

    with patch("gpt_researcher.scraper.pymupdf.pymupdf.PyMuPDFLoader") as mock_loader, \
         patch("gpt_researcher.scraper.pymupdf.pymupdf.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"%PDF-1.4"]
        mock_get.return_value = mock_resp
        mock_loader.return_value.load.return_value = []

        content, images, title = scraper.scrape()

    assert content == ""
    assert images == []
    assert title == ""
