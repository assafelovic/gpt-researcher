"""Regression test: ArxivScraper.scrape degrades to empty result on no docs.

ArxivRetriever returns [] for a query that matches no paper; indexing docs[0]
raised IndexError and aborted the scrape instead of returning ("", [], "").
"""

from unittest.mock import MagicMock, patch

import gpt_researcher.scraper.arxiv.arxiv as arxiv_mod
from gpt_researcher.scraper.arxiv.arxiv import ArxivScraper


def test_scrape_returns_empty_when_no_docs():
    scraper = ArxivScraper("https://arxiv.org/abs/does-not-exist")
    fake_retriever = MagicMock()
    fake_retriever.invoke.return_value = []  # no matching paper
    with patch.object(arxiv_mod, "ArxivRetriever", return_value=fake_retriever):
        content, images, title = scraper.scrape()
    assert content == ""
    assert images == []
    assert title == ""


def test_scrape_returns_doc_when_present():
    scraper = ArxivScraper("https://arxiv.org/abs/1234.5678")
    doc = MagicMock()
    doc.page_content = "Body text"
    doc.metadata = {"Published": "2024", "Authors": "A. Author", "Title": "A Paper"}
    fake_retriever = MagicMock()
    fake_retriever.invoke.return_value = [doc]
    with patch.object(arxiv_mod, "ArxivRetriever", return_value=fake_retriever):
        content, images, title = scraper.scrape()
    assert "Body text" in content
    assert title == "A Paper"
