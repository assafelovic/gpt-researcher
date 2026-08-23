"""Regression test: ArxivScraper.scrape degrades to empty result on no docs.

Empty client results / empty links must not abort the scrape pipeline.
"""

import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

ARXIV_PATH = (
    Path(__file__).resolve().parents[1]
    / "gpt_researcher"
    / "scraper"
    / "arxiv"
    / "arxiv.py"
)
spec = importlib.util.spec_from_file_location("arxiv_scraper_mod", ARXIV_PATH)
arxiv_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arxiv_mod)
ArxivScraper = arxiv_mod.ArxivScraper


def _install_fake_arxiv(papers):
    """Install a fake `arxiv` module returning *papers* from Client.results."""

    class _FakeClient:
        def results(self, search):
            return iter(papers)

    fake = ModuleType("arxiv")
    fake.Client = lambda *a, **k: _FakeClient()
    fake.Search = MagicMock()
    sys.modules["arxiv"] = fake
    return fake


def test_scrape_returns_empty_when_no_paper():
    scraper = ArxivScraper("https://arxiv.org/abs/0000.00000")
    _install_fake_arxiv([])
    try:
        content, images, title = scraper.scrape()
    finally:
        sys.modules.pop("arxiv", None)
    assert content == ""
    assert images == []
    assert title == ""


def test_scrape_returns_empty_when_link_empty():
    scraper = ArxivScraper("")
    content, images, title = scraper.scrape()
    assert content == ""
    assert images == []
    assert title == ""


def test_scrape_returns_doc_when_present():
    scraper = ArxivScraper("https://arxiv.org/abs/1234.5678")
    paper = SimpleNamespace(
        authors=[SimpleNamespace(name="A. Author")],
        published=SimpleNamespace(date=lambda: date(2024, 1, 1)),
        summary="Body text",
        title="A Paper",
    )
    _install_fake_arxiv([paper])
    try:
        content, images, title = scraper.scrape()
    finally:
        sys.modules.pop("arxiv", None)
    assert "Body text" in content
    assert title == "A Paper"
