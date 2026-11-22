"""Regression and unit tests for Duckduckgo retriever query_domains and max_results handling."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "duckduckgo" / "duckduckgo.py"


# Drop the stubs below once loaded, so they can't leak into later tests.
@patch.dict(sys.modules)
def _load_duckduckgo_module():
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


class TestDuckduckgoQueryDomains(unittest.TestCase):
    def test_duckduckgo_query_domains_applied(self):
        mod = _load_duckduckgo_module()
        Duckduckgo = mod.Duckduckgo
        retriever = Duckduckgo.__new__(Duckduckgo)
        retriever.query = "python async"
        retriever.query_domains = ["docs.python.org", "github.com"]
        retriever.ddg = MagicMock()
        retriever.ddg.text.return_value = []

        retriever.search()

        self.assertTrue(retriever.ddg.text.called)
        sent_query = retriever.ddg.text.call_args[0][0]
        self.assertEqual(
            sent_query,
            "(site:docs.python.org OR site:github.com) python async",
        )

    def test_duckduckgo_query_domains_empty_or_none(self):
        mod = _load_duckduckgo_module()
        Duckduckgo = mod.Duckduckgo
        retriever = Duckduckgo.__new__(Duckduckgo)
        retriever.query = "python async"
        retriever.query_domains = []
        retriever.ddg = MagicMock()
        retriever.ddg.text.return_value = []

        retriever.search()
        self.assertEqual(retriever.ddg.text.call_args[0][0], "python async")

        retriever.query_domains = None
        retriever.search()
        self.assertEqual(retriever.ddg.text.call_args[0][0], "python async")

    def test_duckduckgo_query_domains_filters_empty_strings(self):
        mod = _load_duckduckgo_module()
        Duckduckgo = mod.Duckduckgo
        retriever = Duckduckgo.__new__(Duckduckgo)
        retriever.query = "python async"
        retriever.query_domains = ["", "   ", "example.com"]
        retriever.ddg = MagicMock()
        retriever.ddg.text.return_value = []

        retriever.search()
        self.assertEqual(
            retriever.ddg.text.call_args[0][0],
            "(site:example.com) python async",
        )

    def test_duckduckgo_non_positive_max_results_returns_empty(self):
        mod = _load_duckduckgo_module()
        Duckduckgo = mod.Duckduckgo
        retriever = Duckduckgo.__new__(Duckduckgo)
        retriever.query = "python async"
        retriever.query_domains = ["docs.python.org"]
        retriever.ddg = MagicMock()

        self.assertEqual(retriever.search(max_results=0), [])
        self.assertEqual(retriever.search(max_results=-1), [])
        retriever.ddg.text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
