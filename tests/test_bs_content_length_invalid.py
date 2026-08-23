"""BeautifulSoupScraper must ignore invalid Content-Length headers."""

import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock

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

utils_mod = T.ModuleType("gpt_researcher.scraper.utils")
utils_mod.get_relevant_images = lambda *a, **k: []
utils_mod.extract_title = lambda soup: "T"
utils_mod.get_text_from_soup = lambda soup: "body" * 40
utils_mod.clean_soup = lambda soup: soup
sys.modules["gpt_researcher.scraper.utils"] = utils_mod

_PATH = root / "gpt_researcher" / "scraper" / "beautiful_soup" / "beautiful_soup.py"
_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.scraper.beautiful_soup.beautiful_soup", _PATH
)
bs_pkg = T.ModuleType("gpt_researcher.scraper.beautiful_soup")
bs_pkg.__path__ = [str(root / "gpt_researcher" / "scraper" / "beautiful_soup")]
sys.modules["gpt_researcher.scraper.beautiful_soup"] = bs_pkg
_mod = importlib.util.module_from_spec(_spec)
sys.modules["gpt_researcher.scraper.beautiful_soup.beautiful_soup"] = _mod
_spec.loader.exec_module(_mod)
BeautifulSoupScraper = _mod.BeautifulSoupScraper


# Restore the real package; the symbols imported above are already bound.
for _name in [k for k in sys.modules if k not in _SYS_MODULES_SNAPSHOT]:
    del sys.modules[_name]
sys.modules.update(_SYS_MODULES_SNAPSHOT)

class _Resp:
    status_code = 200
    headers = {"Content-Type": "text/html; charset=utf-8", "Content-Length": "not-a-number"}
    content = b"<html><body>hi</body></html>"
    encoding = "utf-8"


def test_invalid_content_length_still_fetches():
    session = MagicMock()
    session.get.return_value = _Resp()
    content, images, title = BeautifulSoupScraper("https://example.com", session).scrape()
    assert "body" in content
    assert title == "T"
    session.get.assert_called()
