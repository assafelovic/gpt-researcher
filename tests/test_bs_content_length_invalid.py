"""BeautifulSoupScraper must ignore invalid Content-Length headers."""

import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock

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
