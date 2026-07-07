"""Regression tests for CRWRetriever (fastCRW) result normalization.

Without the fix, a source missing the ``url`` key raises a KeyError that is
swallowed by the broad ``except`` in ``search()`` — discarding every other
(valid) source in the same response and returning an empty list.
"""
import importlib.util
import os
import pathlib
from unittest.mock import patch

# Import the module directly to avoid importing the heavy gpt_researcher package.
_CRW_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher" / "retrievers" / "crw" / "crw.py"
)
_spec = importlib.util.spec_from_file_location("_crw_under_test", _CRW_PATH)
_crw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_crw)
CRWRetriever = _crw.CRWRetriever


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@patch.dict(os.environ, {"CRW_API_KEY": "test-key"})
def test_crw_skips_sources_missing_url():
    payload = {
        "success": True,
        "data": [
            {"url": "https://a.example", "markdown": "ma"},
            {"url": "https://b.example", "description": "db"},  # no markdown
            {"markdown": "orphan"},  # no url -> skipped, must not abort the rest
        ],
    }
    with patch.object(_crw.requests, "post", return_value=_FakeResp(payload)):
        results = CRWRetriever("q").search()

    assert results == [
        {"href": "https://a.example", "body": "ma"},
        {"href": "https://b.example", "body": "db"},
    ]
