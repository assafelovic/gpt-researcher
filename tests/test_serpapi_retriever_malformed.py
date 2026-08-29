"""Regression tests for SerpApiSearch result normalization.

Without the fix, a response missing ``organic_results`` raises a KeyError, and
a single result missing ``title``/``link``/``snippet`` raises a KeyError that
aborts the whole ``search()`` call.
"""
import importlib.util
import os
import pathlib
import sys
import types
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
RETRIEVERS_DIR = ROOT / "gpt_researcher" / "retrievers"

# Set up parent packages so relative imports (from ..utils import ...) work
sys.modules.setdefault("gpt_researcher", types.ModuleType("gpt_researcher"))
ret_pkg = types.ModuleType("gpt_researcher.retrievers")
sys.modules.setdefault("gpt_researcher.retrievers", ret_pkg)

# Load utils first (needed for append_exclude_terms import in serpapi.py)
_utils_path = RETRIEVERS_DIR / "utils.py"
_utils_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.retrievers.utils", _utils_path
)
_utils_mod = importlib.util.module_from_spec(_utils_spec)
_utils_mod.__package__ = "gpt_researcher.retrievers"
sys.modules["gpt_researcher.retrievers.utils"] = _utils_mod
ret_pkg.utils = _utils_mod
_utils_spec.loader.exec_module(_utils_mod)

# Now load serpapi with proper package context
_SERPAPI_PATH = RETRIEVERS_DIR / "serpapi" / "serpapi.py"
_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.retrievers.serpapi.serpapi", _SERPAPI_PATH
)
_serpapi = importlib.util.module_from_spec(_spec)
_serpapi.__package__ = "gpt_researcher.retrievers.serpapi"
sys.modules[_spec.name] = _serpapi
_spec.loader.exec_module(_serpapi)
SerpApiSearch = _serpapi.SerpApiSearch


class _FakeResp:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload

    def json(self):
        return self._payload


@patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
def test_serpapi_skips_results_missing_keys():
    payload = {
        "organic_results": [
            {"title": "A", "link": "https://a.example", "snippet": "sa"},
            {"title": "B", "link": "https://b.example"},  # missing snippet
            {"link": "https://c.example"},  # missing title + snippet
            {"title": "D", "snippet": "sd"},  # missing link -> skipped
        ]
    }
    with patch.object(_serpapi.requests, "get", return_value=_FakeResp(payload)):
        results = SerpApiSearch("q").search()

    assert len(results) == 3
    assert results[0] == {"title": "A", "href": "https://a.example", "body": "sa"}
    assert results[1]["body"] == ""
    assert results[2]["title"] == ""


@patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
def test_serpapi_no_organic_results_returns_empty():
    with patch.object(_serpapi.requests, "get", return_value=_FakeResp({})):
        assert SerpApiSearch("q").search() == []
