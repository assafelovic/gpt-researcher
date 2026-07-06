"""Regression tests for BingSearch result normalization.

Without the fix, a single result missing an expected key (``url``/``name``/
``snippet``) raises a KeyError that aborts the whole ``search()`` call, and a
response without a ``webPages`` block raises a KeyError instead of returning [].
"""
import importlib.util
import json
import os
import pathlib
from unittest.mock import patch

# Import the module directly to avoid importing the heavy gpt_researcher package
# (which pulls optional deps like json_repair at import time).
_BING_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher" / "retrievers" / "bing" / "bing.py"
)
_spec = importlib.util.spec_from_file_location("_bing_under_test", _BING_PATH)
_bing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bing)
BingSearch = _bing.BingSearch


class _FakeResp:
    def __init__(self, payload):
        self.text = json.dumps(payload)


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bing_skips_results_missing_keys():
    payload = {
        "webPages": {
            "value": [
                {"name": "A", "url": "https://a.example", "snippet": "sa"},
                {"name": "B", "url": "https://b.example"},  # missing snippet
                {"url": "https://c.example"},  # missing name + snippet
            ]
        }
    }
    with patch.object(_bing.requests, "get", return_value=_FakeResp(payload)):
        results = BingSearch("q").search()

    assert len(results) == 3
    assert results[0] == {"title": "A", "href": "https://a.example", "body": "sa"}
    assert results[1]["body"] == ""
    assert results[2]["title"] == ""


@patch.dict(os.environ, {"BING_API_KEY": "test-key"})
def test_bing_no_webpages_returns_empty():
    with patch.object(_bing.requests, "get", return_value=_FakeResp({})):
        assert BingSearch("q").search() == []
