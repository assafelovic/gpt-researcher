"""SerperSearch must tolerate non-dict JSON payloads."""
import importlib.util
import json
import os
import pathlib
from unittest.mock import patch

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "serper"
    / "serper.py"
)
_spec = importlib.util.spec_from_file_location("_serper_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SerperSearch = _mod.SerperSearch


class _FakeResp:
    def __init__(self, payload):
        self.text = json.dumps(payload) if not isinstance(payload, str) else payload


@patch.dict(os.environ, {"SERPER_API_KEY": "test-key"})
def test_serper_list_payload_returns_empty():
    with patch.object(_mod.requests, "request", return_value=_FakeResp([{"link": "x"}])):
        assert SerperSearch("q").search() == []


@patch.dict(os.environ, {"SERPER_API_KEY": "test-key"})
def test_serper_string_payload_returns_empty():
    with patch.object(_mod.requests, "request", return_value=_FakeResp('"oops"')):
        assert SerperSearch("q").search() == []


@patch.dict(os.environ, {"SERPER_API_KEY": "test-key"})
def test_serper_happy_path():
    payload = {
        "organic": [
            {"title": "A", "link": "https://a.example", "snippet": "s"},
            "bad-row",
            {"title": "NoLink"},
        ]
    }
    with patch.object(_mod.requests, "request", return_value=_FakeResp(payload)):
        results = SerperSearch("q").search()
    assert results == [{"title": "A", "href": "https://a.example", "body": "s"}]
