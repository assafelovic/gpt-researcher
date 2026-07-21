"""SearchApi organic_results must tolerate partial / non-dict payloads.

Bare ``search_results["organic_results"]`` and ``result["link"]`` raise on
error-rate-limit stubs, list envelopes, and rows missing title/snippet.
Downstream research expects a list of {title, href, body} dicts, not a crash.
"""

import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "searchapi" / "searchapi.py"


def _load():
    requests_mod = types.ModuleType("requests")
    requests_mod.get = MagicMock()
    sys.modules["requests"] = requests_mod

    for key in list(sys.modules):
        if "searchapi.searchapi" in key or key.endswith("searchapi_testmod"):
            sys.modules.pop(key, None)

    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.searchapi.searchapi_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    with patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"}, clear=False):
        spec.loader.exec_module(mod)
    return mod, requests_mod


class SearchApiOrganicGuards(unittest.TestCase):
    def test_skips_non_dict_rows_and_missing_links(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "organic_results": [
                {"title": "A", "link": "https://a.example", "snippet": "sa"},
                "bad-row",
                {"title": "No link"},
                None,
                {
                    "title": "B",
                    "link": "https://www.youtube.com/watch?v=1",
                    "snippet": "yt",
                },
                {"link": "https://b.example"},  # missing title/snippet OK
            ]
        }
        requests_mod.get.return_value = resp
        with patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"}):
            out = mod.SearchApiSearch("q").search(max_results=10)
        self.assertEqual(
            out,
            [
                {
                    "title": "A",
                    "href": "https://a.example",
                    "body": "sa",
                },
                {
                    "title": "",
                    "href": "https://b.example",
                    "body": "",
                },
            ],
        )

    def test_non_dict_json_returns_empty(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = ["not", "a", "dict"]
        requests_mod.get.return_value = resp
        with patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"}):
            self.assertEqual(mod.SearchApiSearch("q").search(), [])

    def test_missing_organic_results_key_returns_empty(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"error": "rate limited"}
        requests_mod.get.return_value = resp
        with patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"}):
            self.assertEqual(mod.SearchApiSearch("q").search(), [])

    def test_organic_results_non_list_returns_empty(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"organic_results": {"oops": True}}
        requests_mod.get.return_value = resp
        with patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test-key"}):
            self.assertEqual(mod.SearchApiSearch("q").search(), [])


if __name__ == "__main__":
    unittest.main()
