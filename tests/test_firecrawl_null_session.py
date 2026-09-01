"""FireCrawl.scrape must work when session is None (no AttributeError)."""

import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock, patch

# These stubs are only needed while the module under test is being loaded.
# Left in sys.modules they replace the real gpt_researcher package for every
# test module collected afterwards, which turns the whole suite's collection
# into "cannot import name ... (unknown location)". Snapshot here, restore
# below once the load is done.
_SYS_MODULES_SNAPSHOT = dict(sys.modules)
# Only stub bs4 when it is genuinely absent. setdefault() returns the real
# module when bs4 is already imported, and the next line then replaced the
# real BeautifulSoup with a MagicMock for the entire process -- which made
# tests/test_scraper_extract_title.py fail once both were collected together.
if "bs4" not in sys.modules:
    _bs4_stub = types.ModuleType("bs4")
    _bs4_stub.BeautifulSoup = MagicMock
    sys.modules["bs4"] = _bs4_stub

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


# Restore the real package; the symbols imported above are already bound.
for _name in [k for k in sys.modules if k not in _SYS_MODULES_SNAPSHOT]:
    del sys.modules[_name]
sys.modules.update(_SYS_MODULES_SNAPSHOT)

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
