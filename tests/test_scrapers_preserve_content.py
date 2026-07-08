"""Regression tests: scrapers must return successfully-extracted primary content
even when the best-effort image/title enrichment (a second, direct page fetch)
fails.

The enrichment step fetches the page directly, so it fails on exactly the
bot-blocked / JS-only / slow sites these scrapers exist to handle (Tavily is
used precisely because a plain request is rejected). A failure there must not
discard the content the primary extractor already produced.
"""

from unittest.mock import MagicMock, patch


def test_tavily_extract_returns_content_when_enrichment_fetch_fails(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    from gpt_researcher.scraper.tavily_extract.tavily_extract import TavilyExtract

    session = MagicMock()
    session.get.side_effect = Exception("403 Forbidden")  # the secondary fetch is blocked

    scraper = TavilyExtract("https://example.com/blocked", session=session)
    scraper.tavily_client = MagicMock()
    scraper.tavily_client.extract.return_value = {
        "failed_results": [],
        "results": [{"raw_content": "PRIMARY CONTENT"}],
    }

    content, image_urls, title = scraper.scrape()

    assert content == "PRIMARY CONTENT"  # returned "" on main
    assert image_urls == []
    assert title == ""


def test_web_base_loader_returns_content_when_enrichment_fetch_fails():
    from gpt_researcher.scraper.web_base_loader.web_base_loader import WebBaseLoaderScraper

    session = MagicMock()
    session.get.side_effect = Exception("403 Forbidden")  # the secondary fetch is blocked

    scraper = WebBaseLoaderScraper("https://example.com/blocked", session=session)

    doc = MagicMock()
    doc.page_content = "PRIMARY CONTENT"
    with patch("langchain_community.document_loaders.WebBaseLoader") as web_base_loader:
        web_base_loader.return_value.load.return_value = [doc]
        content, image_urls, title = scraper.scrape()

    assert content == "PRIMARY CONTENT"  # returned "" on main
    assert image_urls == []
    assert title == ""
