import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "nestdaddy" / "nestdaddy.py"


# Drop the stubs below once loaded, so they can't leak into later tests.
@patch.dict(sys.modules)
def _load():
    requests_mod = types.ModuleType("requests")
    requests_mod.get = MagicMock()
    sys.modules["requests"] = requests_mod
    for key in list(sys.modules):
        if "nestdaddy.nestdaddy" in key:
            sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.nestdaddy.nestdaddy_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, requests_mod


def _response(payload):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


class NestDaddyRetrieverTests(unittest.TestCase):
    def test_missing_key_raises(self):
        mod, _ = _load()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception) as ctx:
                mod.NestDaddySearch("q")
        self.assertIn("NESTDADDY_API_KEY", str(ctx.exception))

    def test_key_from_headers(self):
        mod, _ = _load()
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(mod.NestDaddySearch("q", headers={"nestdaddy_api_key": "h"}).api_key, "h")

    def test_sends_key_query_and_limit(self):
        mod, requests_mod = _load()
        requests_mod.get.return_value = _response({"success": True, "results": []})
        with patch.dict(os.environ, {"NESTDADDY_API_KEY": "k"}):
            mod.NestDaddySearch("ai agents").search(max_results=4)
        args, kwargs = requests_mod.get.call_args
        self.assertEqual(args[0], "https://nestdaddy.com/api/v1/search")
        self.assertEqual(kwargs["headers"], {"X-API-Key": "k"})
        self.assertEqual(kwargs["params"], {"q": "ai agents", "limit": 4})

    def test_normalizes_and_skips_malformed(self):
        mod, requests_mod = _load()
        requests_mod.get.return_value = _response({
            "success": True,
            "results": [
                {"title": "A", "url": "https://a.example/x", "snippet": "Snip A"},
                {"title": "no url", "snippet": "x"},
                "bad",
                {"title": "Bad scheme", "url": "javascript:alert(1)", "snippet": "x"},
                {"title": "News", "url": "https://b.example/n", "description": "Desc B"},
            ],
        })
        with patch.dict(os.environ, {"NESTDADDY_API_KEY": "k"}):
            out = mod.NestDaddySearch("q").search(max_results=10)
        self.assertEqual(out, [
            {"title": "A", "href": "https://a.example/x", "body": "Snip A"},
            {"title": "News", "href": "https://b.example/n", "body": "Desc B"},
        ])

    def test_respects_max_results(self):
        mod, requests_mod = _load()
        rows = [{"title": str(i), "url": f"https://e.example/{i}", "snippet": "s"} for i in range(10)]
        requests_mod.get.return_value = _response({"success": True, "results": rows})
        with patch.dict(os.environ, {"NESTDADDY_API_KEY": "k"}):
            out = mod.NestDaddySearch("q").search(max_results=3)
        self.assertEqual(len(out), 3)

    def test_non_positive_or_invalid_max_results_returns_empty(self):
        mod, requests_mod = _load()
        with patch.dict(os.environ, {"NESTDADDY_API_KEY": "k"}):
            for value in (0, -1, "x", None):
                self.assertEqual(mod.NestDaddySearch("q").search(max_results=value), [])
        requests_mod.get.assert_not_called()

    def test_query_domains_filter_results(self):
        mod, requests_mod = _load()
        requests_mod.get.return_value = _response({
            "success": True,
            "results": [
                {"title": "Keep", "url": "https://docs.python.org/3/", "snippet": "k"},
                {"title": "Keep sub", "url": "https://www.python.org/about", "snippet": "k"},
                {"title": "Drop", "url": "https://other.example/", "snippet": "d"},
            ],
        })
        with patch.dict(os.environ, {"NESTDADDY_API_KEY": "k"}):
            out = mod.NestDaddySearch("q", query_domains=["python.org"]).search(max_results=5)
        self.assertEqual([r["title"] for r in out], ["Keep", "Keep sub"])
        self.assertEqual(requests_mod.get.call_args.kwargs["params"]["limit"], 15)

    def test_malformed_payloads_return_empty(self):
        mod, requests_mod = _load()
        with patch.dict(os.environ, {"NESTDADDY_API_KEY": "k"}):
            for payload in (["list"], {"success": False, "error": "quota"}, {"results": "oops"}, {"results": None}):
                requests_mod.get.return_value = _response(payload)
                self.assertEqual(mod.NestDaddySearch("q").search(), [])

    def test_error_returns_empty(self):
        mod, requests_mod = _load()
        requests_mod.get.side_effect = Exception("boom")
        with patch.dict(os.environ, {"NESTDADDY_API_KEY": "k"}):
            self.assertEqual(mod.NestDaddySearch("q").search(), [])


if __name__ == "__main__":
    unittest.main()
