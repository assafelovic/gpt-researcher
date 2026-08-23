"""WebBaseLoaderScraper keeps already-extracted content when image/title enrichment fails."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "scraper" / "web_base_loader" / "web_base_loader.py"


def _load(get_relevant_images=lambda soup, link: []):
    bs4 = types.ModuleType("bs4")

    class BeautifulSoup:
        def __init__(self, *a, **k):
            pass

    bs4.BeautifulSoup = BeautifulSoup
    sys.modules["bs4"] = bs4
    req = types.ModuleType("requests")
    req.Session = object
    sys.modules.setdefault("requests", req)

    pkg = types.ModuleType("gpt_researcher")
    scraper = types.ModuleType("gpt_researcher.scraper")
    utils = types.ModuleType("gpt_researcher.scraper.utils")
    utils.get_relevant_images = get_relevant_images
    utils.extract_title = lambda soup: "T"
    sys.modules["gpt_researcher"] = pkg
    sys.modules["gpt_researcher.scraper"] = scraper
    sys.modules["gpt_researcher.scraper.utils"] = utils

    lc = types.ModuleType("langchain_community")
    lcd = types.ModuleType("langchain_community.document_loaders")

    class WebBaseLoader:
        def __init__(self, link):
            self.link = link
            self.requests_kwargs = {}

        def load(self):
            return [types.SimpleNamespace(page_content="real page content")]

    lcd.WebBaseLoader = WebBaseLoader
    sys.modules["langchain_community"] = lc
    sys.modules["langchain_community.document_loaders"] = lcd

    wpkg = types.ModuleType("gpt_researcher.scraper.web_base_loader")
    sys.modules["gpt_researcher.scraper.web_base_loader"] = wpkg

    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.scraper.web_base_loader.web_base_loader", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class WebBaseLoaderEnrichmentGuard(unittest.TestCase):
    def test_keeps_content_when_enrichment_fetch_raises(self):
        mod = _load()
        session = MagicMock()
        session.get.side_effect = ConnectionError("simulated transient network error")
        scraper = mod.WebBaseLoaderScraper("https://ex.com", session=session)

        content, images, title = scraper.scrape()

        self.assertEqual(content, "real page content")
        self.assertEqual(images, [])
        self.assertEqual(title, "")

    def test_keeps_content_when_enrichment_parsing_raises(self):
        def boom(soup, link):
            raise ValueError("malformed page")

        mod = _load(get_relevant_images=boom)
        session = MagicMock()
        resp = MagicMock()
        resp.content = b"<html></html>"
        session.get.return_value = resp
        scraper = mod.WebBaseLoaderScraper("https://ex.com", session=session)

        content, images, title = scraper.scrape()

        self.assertEqual(content, "real page content")
        self.assertEqual(images, [])
        self.assertEqual(title, "")


if __name__ == "__main__":
    unittest.main()
