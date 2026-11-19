import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "helve" / "helve.py"


@patch.dict(sys.modules)
def _load():
    requests_mod = types.ModuleType("requests")
    requests_mod.post = MagicMock()
    sys.modules["requests"] = requests_mod
    for key in list(sys.modules):
        if "helve.helve" in key:
            sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.helve.helve_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    with patch.dict(os.environ, {"HELVE_API_KEY": "sk_live_test"}):
        spec.loader.exec_module(mod)
    return mod, requests_mod


class HelveRetrieverTests(unittest.TestCase):
    def test_normalizes_snippets_and_skips_malformed(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {
            "id": "srch_1",
            "provider": "fusion",
            "results": [
                {"url": "https://a.example", "snippets": ["Part 1", "Part 2"]},
                {"snippets": ["missing url"]},
                "bad-entry",
                {"url": "https://b.example", "summary": "Summary B"},
                {"url": "https://c.example", "full_text": "Full C"},
            ],
        }
        requests_mod.post.return_value = resp
        with patch.dict(os.environ, {"HELVE_API_KEY": "sk_live_test"}):
            out = mod.HelveSearch(
                "ai agents",
                headers={"helve_provider": "fusion"},
                query_domains=["docs.python.org"],
            ).search(max_results=10)

        self.assertEqual(
            out,
            [
                {"href": "https://a.example", "body": "Part 1\nPart 2"},
                {"href": "https://b.example", "body": "Summary B"},
                {"href": "https://c.example", "body": "Full C"},
            ],
        )
        _, kwargs = requests_mod.post.call_args
        self.assertEqual(kwargs["json"]["provider"], "fusion")
        self.assertEqual(kwargs["json"]["include_domains"], ["docs.python.org"])

    def test_missing_api_key_raises(self):
        mod, _ = _load()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception) as ctx:
                mod.HelveSearch("q")
        self.assertIn("HELVE_API_KEY", str(ctx.exception))

    def test_error_returns_empty(self):
        mod, requests_mod = _load()
        requests_mod.post.side_effect = Exception("network error")
        with patch.dict(os.environ, {"HELVE_API_KEY": "sk_live_test"}):
            self.assertEqual(mod.HelveSearch("q").search(), [])


if __name__ == "__main__":
    unittest.main()
