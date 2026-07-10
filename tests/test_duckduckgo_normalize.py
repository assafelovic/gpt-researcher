import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "duckduckgo" / "duckduckgo.py"


def _load_duckduckgo_module():
    # Load the module file directly so we never import gpt_researcher package
    # (pulling json_repair and other heavy deps is unrelated to this unit).
    utils_mod = types.ModuleType("gpt_researcher.retrievers.utils")
    utils_mod.check_pkg = lambda *a, **k: None
    pkg = types.ModuleType("gpt_researcher")
    retrievers = types.ModuleType("gpt_researcher.retrievers")
    sys.modules.setdefault("gpt_researcher", pkg)
    sys.modules.setdefault("gpt_researcher.retrievers", retrievers)
    sys.modules["gpt_researcher.retrievers.utils"] = utils_mod

    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.duckduckgo.duckduckgo", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class DuckduckgoNormalizeTests(unittest.TestCase):
    def test_normalizes_href_body_shape(self):
        mod = _load_duckduckgo_module()
        Duckduckgo = mod.Duckduckgo
        retriever = Duckduckgo.__new__(Duckduckgo)
        retriever.query = "python"
        retriever.query_domains = None
        retriever.ddg = MagicMock()
        retriever.ddg.text.return_value = [
            {"link": "https://example.com/a", "snippet": "A", "title": "One"},
            {"url": "https://example.com/b", "description": "B"},
            {"href": "https://example.com/c", "body": "C", "title": "Three"},
            {"title": "no-url"},
        ]
        results = Duckduckgo.search(retriever, max_results=5)
        self.assertEqual(
            results,
            [
                {"href": "https://example.com/a", "body": "A", "title": "One"},
                {"href": "https://example.com/b", "body": "B"},
                {"href": "https://example.com/c", "body": "C", "title": "Three"},
            ],
        )

    def test_empty_or_error_returns_list(self):
        mod = _load_duckduckgo_module()
        Duckduckgo = mod.Duckduckgo
        retriever = Duckduckgo.__new__(Duckduckgo)
        retriever.query = "python"
        retriever.query_domains = None
        retriever.ddg = MagicMock()
        retriever.ddg.text.side_effect = Exception("network")
        self.assertEqual(Duckduckgo.search(retriever), [])

        retriever.ddg.text.side_effect = None
        retriever.ddg.text.return_value = None
        self.assertEqual(Duckduckgo.search(retriever), [])


if __name__ == "__main__":
    unittest.main()
