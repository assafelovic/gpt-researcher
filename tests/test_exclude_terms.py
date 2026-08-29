"""Tests for exclude-terms feature across retrievers.

Covers:
- append_exclude_terms helper (quoting rules)
- supports_exclude_terms signature check
- Application in each implementing retriever (google, brave, serper, serpapi, searchapi, searx)
- Call-site tolerant-pass behavior
"""
import importlib.util
import inspect
import os
import pathlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
RETRIEVERS_DIR = ROOT / "gpt_researcher" / "retrievers"


# ---------------------------------------------------------------------------
# Helpers to load modules directly (avoids heavy gpt_researcher imports)
# ---------------------------------------------------------------------------

def _load_utils_module():
    """Load retrievers/utils.py directly without importing the package."""
    utils_path = RETRIEVERS_DIR / "utils.py"
    spec = importlib.util.spec_from_file_location("_utils_under_test", utils_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_utils_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_retriever_module(name: str, class_name: str):
    """Load a retriever module directly with proper package setup for relative imports."""
    # Set up the parent packages so relative imports (from ..utils import ...) work
    pkg = types.ModuleType("gpt_researcher")
    sys.modules.setdefault("gpt_researcher", pkg)

    ret_pkg = types.ModuleType("gpt_researcher.retrievers")
    sys.modules.setdefault("gpt_researcher.retrievers", ret_pkg)
    pkg.retrievers = ret_pkg

    # Load utils first (the real module, so append_exclude_terms is available)
    utils_path = RETRIEVERS_DIR / "utils.py"
    utils_spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.utils", utils_path
    )
    utils_mod = importlib.util.module_from_spec(utils_spec)
    utils_mod.__package__ = "gpt_researcher.retrievers"
    sys.modules["gpt_researcher.retrievers.utils"] = utils_mod
    ret_pkg.utils = utils_mod
    utils_spec.loader.exec_module(utils_mod)

    # Now load the retriever module with proper package context
    module_path = RETRIEVERS_DIR / name / f"{name}.py"
    mod_name = f"gpt_researcher.retrievers.{name}.{name}"
    spec = importlib.util.spec_from_file_location(mod_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = f"gpt_researcher.retrievers.{name}"
    mod.__name__ = mod_name
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod, getattr(mod, class_name)


# ---------------------------------------------------------------------------
# append_exclude_terms tests
# ---------------------------------------------------------------------------

class AppendExcludeTermsTests(unittest.TestCase):
    def setUp(self):
        self.utils = _load_utils_module()
        self.fn = self.utils.append_exclude_terms

    def test_none_returns_query(self):
        self.assertEqual(self.fn("test query", None), "test query")

    def test_empty_list_returns_query(self):
        self.assertEqual(self.fn("test query", []), "test query")

    def test_single_word(self):
        self.assertEqual(self.fn("test query", ["gartner"]), "test query -gartner")

    def test_multi_word_uses_double_quotes(self):
        self.assertEqual(
            self.fn("test query", ["market share"]),
            'test query -"market share"',
        )

    def term_with_double_quote_uses_single_quotes(self):
        self.assertEqual(
            self.fn('test query', ['he said "bad"']),
            "test query -'he said \"bad\"'",
        )

    def test_multiple_exclusions(self):
        self.assertEqual(
            self.fn("How many PCs sold?", ["gartner", "market share"]),
            'How many PCs sold? -gartner -"market share"',
        )

    def test_whitespace_only_skipped(self):
        self.assertEqual(
            self.fn("q", ["  ", "", "ok"]),
            "q -ok",
        )


# ---------------------------------------------------------------------------
# supports_exclude_terms tests
# ---------------------------------------------------------------------------

class SupportsExcludeTermsTests(unittest.TestCase):
    def setUp(self):
        self.utils = _load_utils_module()
        self.fn = self.utils.supports_exclude_terms

    def test_named_param_returns_true(self):
        class WithParam:
            def __init__(self, q, exclude_terms=None):
                pass
        self.assertTrue(self.fn(WithParam))

    def test_no_param_returns_false(self):
        class NoParam:
            def __init__(self, q):
                pass
        self.assertFalse(self.fn(NoParam))

    def test_kwargs_only_returns_false(self):
        class KwargOnly:
            def __init__(self, q, **kwargs):
                pass
        self.assertFalse(self.fn(KwargOnly))


# ---------------------------------------------------------------------------
# Application tests — each implementing retriever applies the suffix
# ---------------------------------------------------------------------------

class RetrieverApplicationTests(unittest.TestCase):
    """Verify that each implementing retriever correctly applies exclude_terms."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test", "GOOGLE_CX_KEY": "test"})
    def test_google_applies_suffix(self):
        mod, cls = _load_retriever_module("google", "GoogleSearch")
        r = cls("python", exclude_terms=["java"])
        self.assertEqual(r.query, "python -java")

    @patch.dict(os.environ, {"BRAVE_API_KEY": "test"})
    def test_brave_applies_suffix(self):
        mod, cls = _load_retriever_module("brave", "BraveSearch")
        r = cls("python", exclude_terms=["java"])
        self.assertEqual(r.query, "python -java")

    @patch.dict(os.environ, {"SERPER_API_KEY": "test"})
    def test_serper_applies_suffix(self):
        mod, cls = _load_retriever_module("serper", "SerperSearch")
        r = cls("python", exclude_terms=["java"])
        self.assertEqual(r.query, "python -java")

    @patch.dict(os.environ, {"SERPAPI_API_KEY": "test"})
    def test_serpapi_applies_suffix(self):
        mod, cls = _load_retriever_module("serpapi", "SerpApiSearch")
        r = cls("python", exclude_terms=["java"])
        self.assertEqual(r.query, "python -java")

    @patch.dict(os.environ, {"SEARCHAPI_API_KEY": "test"})
    def test_searchapi_applies_suffix(self):
        mod, cls = _load_retriever_module("searchapi", "SearchApiSearch")
        r = cls("python", exclude_terms=["java"])
        self.assertEqual(r.query, "python -java")

    @patch.dict(os.environ, {"SEARX_URL": "http://localhost:8080/"})
    def test_searx_applies_suffix(self):
        mod, cls = _load_retriever_module("searx", "SearxSearch")
        r = cls("python", exclude_terms=["java"])
        self.assertEqual(r.query, "python -java")

    # Non-implementing retrievers should NOT have the parameter
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test"})
    def test_tavily_does_not_have_param(self):
        tavily_path = RETRIEVERS_DIR / "tavily" / "tavily_search.py"
        spec = importlib.util.spec_from_file_location("_ret_tavily", tavily_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_ret_tavily"] = mod
        spec.loader.exec_module(mod)
        sig = inspect.signature(mod.TavilySearch.__init__)
        self.assertNotIn("exclude_terms", sig.parameters)

    @patch.dict(os.environ, {"BING_API_KEY": "test"})
    def test_bing_does_not_have_param(self):
        mod, _ = _load_retriever_module("bing", "BingSearch")
        sig = inspect.signature(mod.BingSearch.__init__)
        self.assertNotIn("exclude_terms", sig.parameters)


# ---------------------------------------------------------------------------
# Call-site tolerant-pass tests
# ---------------------------------------------------------------------------

class CallSiteTests(unittest.TestCase):
    """Verify that the call-site logic passes exclude_terms only to supporting retrievers."""

    def setUp(self):
        self.utils = _load_utils_module()
        self.supports = self.utils.supports_exclude_terms

    def test_supporting_retriever_identified(self):
        class Supporting:
            def __init__(self, q, exclude_terms=None):
                pass
        self.assertTrue(self.supports(Supporting))

    def test_non_supporting_retriever_identified(self):
        class NonSupporting:
            def __init__(self, q):
                pass
        self.assertFalse(self.supports(NonSupporting))

    def test_kwargs_only_not_treated_as_supporting(self):
        class KwargOnly:
            def __init__(self, q, **kwargs):
                pass
        self.assertFalse(self.supports(KwargOnly))


if __name__ == "__main__":
    unittest.main()
