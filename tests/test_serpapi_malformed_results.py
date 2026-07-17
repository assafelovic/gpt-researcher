"""SerpApiSearch organic_results must tolerate non-dict / incomplete rows."""

from __future__ import annotations

import importlib.util
import os
import pathlib
from unittest.mock import MagicMock, patch

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "serpapi"
    / "serpapi.py"
)
_spec = importlib.util.spec_from_file_location("_serpapi_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SerpApiSearch = _mod.SerpApiSearch


@patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
def test_serpapi_skips_non_dict_and_empty_link():
    payload = {
        "organic_results": [
            "not-a-dict",
            None,
            {"title": "No link"},
            {
                "title": "Ok",
                "link": "https://ok.example",
                "snippet": "body",
            },
            {
                "title": "YT",
                "link": "https://youtube.com/watch?v=1",
                "snippet": "y",
            },
        ]
    }
    resp = MagicMock(status_code=200)
    resp.json.return_value = payload
    with patch.object(_mod.requests, "get", return_value=resp):
        out = SerpApiSearch("q").search(max_results=10)

    assert out == [
        {"title": "Ok", "href": "https://ok.example", "body": "body"},
    ]


@patch.dict(os.environ, {"SERPAPI_API_KEY": "test-key"})
def test_serpapi_non_list_organic_returns_empty():
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"organic_results": {"oops": True}}
    with patch.object(_mod.requests, "get", return_value=resp):
        assert SerpApiSearch("q").search() == []
