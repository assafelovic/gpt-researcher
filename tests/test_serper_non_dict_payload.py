"""SerperSearch must tolerate non-dict JSON payloads without AttributeError.

A 200 body that parses to a list/str used to crash on ``.get("organic")``.
"""

import importlib.util
import json
import os
import pathlib
from unittest.mock import MagicMock, patch

_SERPER_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "serper"
    / "serper.py"
)
_spec = importlib.util.spec_from_file_location("_serper_under_test", _SERPER_PATH)
_serper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_serper)
SerperSearch = _serper.SerperSearch


class _FakeResp:
    def __init__(self, payload):
        self.text = payload if isinstance(payload, str) else json.dumps(payload)


@patch.dict(os.environ, {"SERPER_API_KEY": "test-key"})
def test_search_returns_list_when_json_is_list():
    with patch.object(_serper.requests, "request", return_value=_FakeResp([{"link": "https://x"}])):
        out = SerperSearch("q").search()
    assert out == []


@patch.dict(os.environ, {"SERPER_API_KEY": "test-key"})
def test_search_returns_list_when_json_is_string():
    with patch.object(_serper.requests, "request", return_value=_FakeResp('"surprise"')):
        out = SerperSearch("q").search()
    assert out == []


@patch.dict(os.environ, {"SERPER_API_KEY": "test-key"})
def test_search_still_parses_organic_dicts():
    payload = {
        "organic": [
            {"title": "T", "link": "https://ex.com", "snippet": "S"},
            "skip-me",
            {"link": ""},
        ]
    }
    with patch.object(_serper.requests, "request", return_value=_FakeResp(payload)):
        out = SerperSearch("q").search()
    assert out == [{"title": "T", "href": "https://ex.com", "body": "S"}]
