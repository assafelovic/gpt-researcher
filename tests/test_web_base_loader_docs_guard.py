"""WebBaseLoaderScraper skips null docs / missing page_content."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "scraper" / "web_base_loader" / "web_base_loader.py"


def _load():
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
    utils.get_relevant_images = lambda soup, link: []
    utils.extract_title = lambda soup: "T"
    sys.modules["gpt_researcher"] = pkg
    sys.modules["gpt_researcher.scraper"] = scraper
    sys.modules["gpt_researcher.scraper.utils"] = utils

    lc = types.ModuleType("langchain_community")
    lcd = types.ModuleType("langchain_community.document_loaders")

    class WebBaseLoader:
        last = None

        def __init__(self, link):
            self.link = link
            self.requests_kwargs = {}
            WebBaseLoader.last = self
            self._docs = []

        def load(self):
            return self._docs

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
    return mod, WebBaseLoader


class WebBaseLoaderDocsGuard(unittest.TestCase):
    def test_skips_none_docs_and_missing_page_content(self):
        mod, WebBaseLoader = _load()
        session = MagicMock()
        resp = MagicMock()
        resp.content = b"<html></html>"
        session.get.return_value = resp
        scraper = mod.WebBaseLoaderScraper("https://ex.com", session=session)

        # Patch loader after import embeds class reference via local import in scrape()
        content_holder = {}

        def run():
            # Force load docs via WebBaseLoader.last after scrape starts — set docs ahead
            print("setup")

        # Inject docs by patching class used inside scrape's import path
        lcd = sys.modules["langchain_community.document_loaders"]

        class Loader:
            def __init__(self, link):
                self.requests_kwargs = {}

            def load(self):
                return [
                    None,
                    object(),  # no page_content
                    types.SimpleNamespace(page_content=None),
                    types.SimpleNamespace(page_content="hello "),
                    types.SimpleNamespace(page_content="world"),
                ]

        lcd.WebBaseLoader = Loader
        text, images, title = scraper.scrape()
        self.assertEqual(text, "hello world")
        self.assertEqual(title, "T")


if __name__ == "__main__":
    unittest.main()
