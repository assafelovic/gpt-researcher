"""PyMuPDFScraper must use the provided session for HTTP PDF downloads (#1847)."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "scraper" / "pymupdf" / "pymupdf.py"


def _load_pymupdf_module():
    # Direct load to avoid packaging gpt_researcher (json_repair etc.).
    pkg = types.ModuleType("gpt_researcher")
    scraper = types.ModuleType("gpt_researcher.scraper")
    pymupdf_pkg = types.ModuleType("gpt_researcher.scraper.pymupdf")
    sys.modules.setdefault("gpt_researcher", pkg)
    sys.modules.setdefault("gpt_researcher.scraper", scraper)
    sys.modules.setdefault("gpt_researcher.scraper.pymupdf", pymupdf_pkg)

    # stub languagе langchain_community loader import path used inside module
    lc = types.ModuleType("langchain_community")
    lcd = types.ModuleType("langchain_community.document_loaders")
    class PyMuPDFLoader:  # placeholder overwritten in patch
        def __init__(self, *a, **k):
            pass
        def load(self):
            return []
    lcd.PyMuPDFLoader = PyMuPDFLoader
    sys.modules.setdefault("langchain_community", lc)
    sys.modules.setdefault("langchain_community.document_loaders", lcd)

    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.scraper.pymupdf.pymupdf", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class PyMuPDFSessionUATests(unittest.TestCase):
    def test_scrape_url_uses_session_get_not_bare_requests(self):
        mod = _load_pymupdf_module()
        session = MagicMock()
        resp = MagicMock()
        resp.iter_content = MagicMock(return_value=[b"%PDF-1.4"])
        resp.raise_for_status = MagicMock()
        session.get.return_value = resp

        scraper = mod.PyMuPDFScraper("https://example.com/doc.pdf", session=session)
        page = MagicMock()
        page.page_content = "hello"
        page.metadata = {"title": "T"}
        with patch.object(mod, "requests") as requests_mod, patch.object(
            mod, "PyMuPDFLoader"
        ) as loader_cls:
            requests_mod.exceptions = __import__("requests").exceptions
            loader_cls.return_value.load.return_value = [page]
            text, images, title = scraper.scrape()

        requests_mod.get.assert_not_called()
        session.get.assert_called()
        self.assertTrue(session.get.call_args.kwargs.get("stream"))
        self.assertIn("hello", text)
        self.assertEqual(title, "T")


if __name__ == "__main__":
    unittest.main()
