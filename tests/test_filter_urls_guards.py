"""Guards for filter_urls against malformed caller input."""
import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

ROOT = pathlib.Path(__file__).resolve().parent.parent
PKG = "gpt_researcher"
if PKG not in sys.modules:
    pkg = types.ModuleType(PKG)
    pkg.__path__ = [str(ROOT / PKG)]
    sys.modules[PKG] = pkg

# Lightweight package stubs so relative imports resolve without full install.
for name, path_tail in (
    (f"{PKG}.utils", "utils"),
    (f"{PKG}.utils.workers", None),
    (f"{PKG}.utils.logger", None),
    (f"{PKG}.scraper", "scraper"),
    (f"{PKG}.config", "config"),
    (f"{PKG}.config.config", None),
    (f"{PKG}.actions", "actions"),
):
    if name not in sys.modules:
        m = types.ModuleType(name)
        if path_tail:
            m.__path__ = [str(ROOT / PKG / path_tail)]
        sys.modules[name] = m

sys.modules[f"{PKG}.utils.workers"].WorkerPool = object
sys.modules[f"{PKG}.utils.logger"].get_formatted_logger = lambda: MagicMock()
sys.modules[f"{PKG}.scraper"].Scraper = object
sys.modules[f"{PKG}.config.config"].Config = object
sys.modules.setdefault("colorama", MagicMock())
sys.modules["colorama"].Fore = SimpleNamespace(RED="", GREEN="")
sys.modules["colorama"].Style = SimpleNamespace(RESET_ALL="")

_PATH = ROOT / "gpt_researcher" / "actions" / "web_scraping.py"
_spec = importlib.util.spec_from_file_location(
    f"{PKG}.actions.web_scraping", _PATH
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
filter_urls = _mod.filter_urls


def _run(coro):
    return asyncio.run(coro)


def test_filter_skips_non_string_urls():
    cfg = SimpleNamespace(excluded_domains=["evil.com"])
    urls = [
        "https://ok.example/a",
        None,
        123,
        "",
        "https://evil.com/x",
        "https://ok.example/b",
    ]
    out = _run(filter_urls(urls, cfg))
    assert out == ["https://ok.example/a", "https://ok.example/b"]


def test_filter_tolerates_none_excluded_domains():
    cfg = SimpleNamespace(excluded_domains=None)
    assert _run(filter_urls(["https://a.example"], cfg)) == ["https://a.example"]


def test_filter_skips_non_string_exclusion_entries():
    cfg = SimpleNamespace(excluded_domains=[None, 1, "bad.example", ""])
    urls = ["https://good.example", "https://bad.example/x"]
    assert _run(filter_urls(urls, cfg)) == ["https://good.example"]


def test_filter_non_list_urls_returns_empty():
    cfg = SimpleNamespace(excluded_domains=[])
    assert _run(filter_urls(None, cfg)) == []
    assert _run(filter_urls("https://not-a-list.example", cfg)) == []
