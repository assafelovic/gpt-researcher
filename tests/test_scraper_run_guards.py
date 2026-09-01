"""Scraper.run must tolerate None/non-dict gather results.

A single failed worker must not raise TypeError/KeyError when filtering
contents, or every successful scrape in the batch is lost.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


def _load_scraper_module():
    # Minimal stubs so scraper.py imports without the full gptr stack.
    root = Path(__file__).resolve().parents[1]
    pkg = types.ModuleType("gpt_researcher")
    pkg.__path__ = [str(root / "gpt_researcher")]
    sys.modules.setdefault("gpt_researcher", pkg)

    utils_workers = types.ModuleType("gpt_researcher.utils.workers")

    class WorkerPool:  # pragma: no cover - type filler
        pass

    utils_workers.WorkerPool = WorkerPool
    sys.modules["gpt_researcher.utils"] = types.ModuleType("gpt_researcher.utils")
    sys.modules["gpt_researcher.utils.workers"] = utils_workers

    scraper_pkg = types.ModuleType("gpt_researcher.scraper")
    scraper_pkg.__path__ = [str(root / "gpt_researcher" / "scraper")]
    # Provide dummy scraper classes referenced by scraper.py imports
    for name in (
        "ArxivScraper",
        "BeautifulSoupScraper",
        "BrowserScraper",
        "FireCrawl",
        "NoDriverScraper",
        "PyMuPDFScraper",
        "TavilyExtract",
        "WebBaseLoaderScraper",
    ):
        setattr(scraper_pkg, name, object)
    sys.modules["gpt_researcher.scraper"] = scraper_pkg

    colorama = types.ModuleType("colorama")
    colorama.Fore = types.SimpleNamespace(YELLOW="")
    colorama.init = lambda *a, **k: None
    sys.modules.setdefault("colorama", colorama)
    sys.modules.setdefault("requests", types.ModuleType("requests"))
    sys.modules["requests"].Session = MagicMock

    path = root / "gpt_researcher" / "scraper" / "scraper.py"
    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.scraper.scraper_mod", path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gpt_researcher.scraper.scraper_mod"] = mod
    # Make relative imports inside scraper.py resolve
    sys.modules["gpt_researcher.scraper"] = scraper_pkg
    # reload with package context
    scraper_pkg.scraper = mod
    # inject for "from . import …"
    import gpt_researcher.scraper as sp  # noqa

    for name in (
        "ArxivScraper",
        "BeautifulSoupScraper",
        "BrowserScraper",
        "FireCrawl",
        "NoDriverScraper",
        "PyMuPDFScraper",
        "TavilyExtract",
        "WebBaseLoaderScraper",
    ):
        setattr(sp, name, object)
    spec.loader.exec_module(mod)
    return mod


class TestScraperRunGuards(unittest.TestCase):
    def test_filters_none_and_non_dict(self):
        mod = _load_scraper_module()
        scraper = mod.Scraper(
            urls=["https://a.example", "https://b.example", "https://c.example"],
            user_agent="ua",
            scraper="bs",
            worker_pool=MagicMock(),
        )

        async def fake_extract(url, session):
            if "a." in url:
                return {"raw_content": "good", "url": url}
            if "b." in url:
                return None
            return "not-a-dict"

        scraper.extract_data_from_url = fake_extract  # type: ignore

        out = asyncio.run(scraper.run())
        self.assertEqual(out, [{"raw_content": "good", "url": "https://a.example"}])

    def test_drops_null_raw_content_dicts(self):
        mod = _load_scraper_module()
        scraper = mod.Scraper(
            urls=["https://a.example"],
            user_agent="ua",
            scraper="bs",
            worker_pool=MagicMock(),
        )

        async def fake_extract(url, session):
            return {"raw_content": None, "url": url}

        scraper.extract_data_from_url = fake_extract  # type: ignore
        out = asyncio.run(scraper.run())
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
