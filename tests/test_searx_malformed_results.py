import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "searx" / "searx.py"


def _load():
    requests_mod = types.ModuleType("requests")
    class RequestException(Exception):
        pass
    exceptions = types.ModuleType("requests.exceptions")
    exceptions.RequestException = RequestException
    requests_mod.exceptions = exceptions
    requests_mod.get = MagicMock()
    sys.modules["requests"] = requests_mod

    for key in list(sys.modules):
        if "searx.searx" in key:
            sys.modules.pop(key, None)

    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.searx.searx_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    with patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"}, clear=False):
        spec.loader.exec_module(mod)
    return mod, requests_mod


class SearxMalformedTests(unittest.TestCase):
    def test_skips_missing_url_and_non_dict_items(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {
            "results": [
                {"url": "https://a.example", "content": "A"},
                {"content": "no url"},
                "bad",
                {"href": "https://b.example", "snippet": "B"},
                None,
            ]
        }
        requests_mod.get.return_value = resp
        with patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"}):
            out = mod.SearxSearch("q").search(max_results=10)
        self.assertEqual(
            out,
            [
                {"href": "https://a.example", "body": "A"},
                {"href": "https://b.example", "body": "B"},
            ],
        )

    def test_non_dict_json_returns_empty(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = ["not", "a", "dict"]
        requests_mod.get.return_value = resp
        with patch.dict(os.environ, {"SEARX_URL": "https://searx.example/"}):
            self.assertEqual(mod.SearxSearch("q").search(), [])


if __name__ == "__main__":
    unittest.main()
