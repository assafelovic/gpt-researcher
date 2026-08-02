"""TavilyExtract keeps content when session is None; guards partial payloads."""
import importlib.util
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _stub_bs4():
    bs4 = types.ModuleType("bs4")
    class BeautifulSoup:
        def __init__(self, *a, **k):
            pass
    bs4.BeautifulSoup = BeautifulSoup
    sys.modules["bs4"] = bs4

ROOT = Path(__file__).resolve().parent.parent
TE_PATH = ROOT / "gpt_researcher" / "scraper" / "tavily_extract" / "tavily_extract.py"
UTILS_PATH = ROOT / "gpt_researcher" / "scraper" / "utils.py"


def _load_tavily_module():
    _stub_bs4()
    # Minimal package graph so relative imports work without heavy agent deps.
    pkg = types.ModuleType("gpt_researcher")
    pkg.__path__ = [str(ROOT / "gpt_researcher")]
    sys.modules["gpt_researcher"] = pkg

    scraper_pkg = types.ModuleType("gpt_researcher.scraper")
    scraper_pkg.__path__ = [str(ROOT / "gpt_researcher" / "scraper")]
    sys.modules["gpt_researcher.scraper"] = scraper_pkg

    u_mod = types.ModuleType("gpt_researcher.scraper.utils")
    u_mod.get_relevant_images = lambda soup, link: [{"src": "x"}]
    u_mod.extract_title = lambda soup: "Title"
    sys.modules["gpt_researcher.scraper.utils"] = u_mod

    te_pkg = types.ModuleType("gpt_researcher.scraper.tavily_extract")
    te_pkg.__path__ = [str(TE_PATH.parent)]
    sys.modules["gpt_researcher.scraper.tavily_extract"] = te_pkg

    name = "gpt_researcher.scraper.tavily_extract.tavily_extract"
    spec = importlib.util.spec_from_file_location(name, TE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    # parent package attribute for relative imports
    mod.__package__ = "gpt_researcher.scraper.tavily_extract"
    spec.loader.exec_module(mod)
    return mod


class _FakeTavily:
    def __init__(self, *a, **k):
        pass

    def extract(self, urls=None):
        return {
            "failed_results": [],
            "results": [{"raw_content": "EXTRACTED BODY"}],
        }


@patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
def test_session_none_keeps_content():
    fake_tavily = SimpleNamespace(TavilyClient=_FakeTavily)
    with patch.dict(sys.modules, {"tavily": fake_tavily}):
        mod = _load_tavily_module()
        content, images, title = mod.TavilyExtract(
            "https://example.com", session=None
        ).scrape()
    assert content == "EXTRACTED BODY"
    assert images == []
    assert title == ""


@patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
def test_malformed_response_returns_empty():
    class Bad:
        def __init__(self, *a, **k):
            pass

        def extract(self, urls=None):
            return ["not-a-dict"]

    with patch.dict(sys.modules, {"tavily": SimpleNamespace(TavilyClient=Bad)}):
        mod = _load_tavily_module()
        scraper = object.__new__(mod.TavilyExtract)
        scraper.link = "https://example.com"
        scraper.session = None
        scraper.tavily_client = Bad()
        assert mod.TavilyExtract.scrape(scraper) == ("", [], "")
