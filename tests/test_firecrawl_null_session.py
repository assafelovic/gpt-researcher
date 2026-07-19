"""FireCrawl.scrape must work when session is None (no AttributeError)."""

import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock, patch

sys.modules.setdefault("bs4", types.ModuleType("bs4"))
sys.modules["bs4"].BeautifulSoup = MagicMock

root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

import types as T

pkg = T.ModuleType("gpt_researcher")
pkg.__path__ = [str(root / "gpt_researcher")]
sys.modules["gpt_researcher"] = pkg
scraper_pkg = T.ModuleType("gpt_researcher.scraper")
scraper_pkg.__path__ = [str(root / "gpt_researcher" / "scraper")]
sys.modules["gpt_researcher.scraper"] = scraper_pkg
fc_pkg = T.ModuleType("gpt_researcher.scraper.firecrawl")
fc_pkg.__path__ = [str(root / "gpt_researcher" / "scraper" / "firecrawl")]
sys.modules["gpt_researcher.scraper.firecrawl"] = fc_pkg

utils_mod = T.ModuleType("gpt_researcher.scraper.utils")
utils_mod.get_relevant_images = lambda soup, link: ["https://img.example/a.png"]
sys.modules["gpt_researcher.scraper.utils"] = utils_mod

_PATH = root / "gpt_researcher" / "scraper" / "firecrawl" / "firecrawl.py"
_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.scraper.firecrawl.firecrawl", _PATH
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["gpt_researcher.scraper.firecrawl.firecrawl"] = _mod
with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "k"}):
    _spec.loader.exec_module(_mod)

FireCrawl = _mod.FireCrawl


class _Meta:
    error = None
    status_code = 200
    title = "Hello"


class _Resp:
    metadata = _Meta()
    markdown = "x" * 150


def test_scrape_with_session_none_returns_content():
    app = MagicMock()
    app.scrape.return_value = _Resp()

    class _AppFactory:
        def __init__(self, *a, **k):
            pass

        def scrape(self, **kwargs):
            return app.scrape(**kwargs)

    with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "k"}), patch.dict(
        sys.modules, {"firecrawl": types.SimpleNamespace(FirecrawlApp=_AppFactory)}
    ):
        # Re-bind constructor path used inside scrape init
        scraper = FireCrawl("https://example.com/page", session=None)
        scraper.firecrawl = app
        content, images, title = scraper.scrape()
    assert content == "x" * 150
    assert images == []
    assert title == "Hello"
    app.scrape.assert_called_once()
