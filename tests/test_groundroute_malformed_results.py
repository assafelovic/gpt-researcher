import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "groundroute" / "groundroute.py"


def _load():
    requests_mod = types.ModuleType("requests")
    requests_mod.post = MagicMock()
    sys.modules["requests"] = requests_mod
    for key in list(sys.modules):
        if "groundroute.groundroute" in key:
            sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.groundroute.groundroute_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    with patch.dict(os.environ, {"GROUNDROUTE_API_KEY": "k"}):
        spec.loader.exec_module(mod)
    return mod, requests_mod


class GroundRouteMalformedTests(unittest.TestCase):
    def test_skips_missing_url(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {
            "results": [
                {"url": "https://a.example", "content": "A"},
                {"content": "no url"},
                "bad",
                {"link": "https://b.example", "snippet": "B"},
            ]
        }
        requests_mod.post.return_value = resp
        with patch.dict(os.environ, {"GROUNDROUTE_API_KEY": "k"}):
            out = mod.GroundRouteSearch("q").search(max_results=10)
        self.assertEqual(
            out,
            [
                {"href": "https://a.example", "body": "A"},
                {"href": "https://b.example", "body": "B"},
            ],
        )

    def test_error_returns_empty(self):
        mod, requests_mod = _load()
        requests_mod.post.side_effect = Exception("boom")
        with patch.dict(os.environ, {"GROUNDROUTE_API_KEY": "k"}):
            self.assertEqual(mod.GroundRouteSearch("q").search(), [])


if __name__ == "__main__":
    unittest.main()
