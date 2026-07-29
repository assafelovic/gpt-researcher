"""Guards for SerpApi organic_results shape and row types."""

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MOD_PATH = ROOT / "gpt_researcher" / "retrievers" / "serpapi" / "serpapi.py"


def _load_serpapi():
    name = "gptr_serpapi_under_test"
    spec = importlib.util.spec_from_file_location(name, MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _search_with_payload(payload):
    mod = _load_serpapi()
    resp = SimpleNamespace(status_code=200, json=lambda: payload)
    with patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"}):
        with patch.object(mod, "requests") as req:
            req.get.return_value = resp
            retriever = mod.SerpApiSearch("q")
            return retriever.search(max_results=5)


def test_non_list_organic_results_returns_empty():
    assert _search_with_payload({"organic_results": {"link": "https://x"}}) == []


def test_skips_non_dict_rows_and_missing_links():
    out = _search_with_payload(
        {
            "organic_results": [
                "bad",
                {"title": "no link"},
                {"title": "ok", "link": "https://example.com", "snippet": "s"},
                {"title": "yt", "link": "https://youtube.com/watch?v=1"},
            ]
        }
    )
    assert out == [
        {"title": "ok", "href": "https://example.com", "body": "s"},
    ]
