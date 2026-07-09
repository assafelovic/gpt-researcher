"""GoogleSearch must tolerate malformed CSE items / response shapes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.google.google import GoogleSearch


def _searcher():
    g = GoogleSearch.__new__(GoogleSearch)
    g.query = "q"
    g.headers = {}
    g.query_domains = None
    g.api_key = "k"
    g.cx_key = "cx"
    return g


def test_google_skips_non_dict_and_missing_link():
    g = _searcher()
    payload = {
        "items": [
            {"title": "A", "link": "https://a.example", "snippet": "sa"},
            "not-a-dict",
            {"title": "No link"},
            {"title": "YT", "link": "https://youtube.com/watch?v=1", "snippet": "y"},
            {"link": "https://b.example"},  # title/snippet optional
        ]
    }
    resp = MagicMock(status_code=200, text='{}')
    with patch(
        "gpt_researcher.retrievers.google.google.requests.get", return_value=resp
    ), patch(
        "gpt_researcher.retrievers.google.google.json.loads", return_value=payload
    ):
        out = g.search(max_results=10)

    assert out == [
        {"title": "A", "href": "https://a.example", "body": "sa"},
        {"title": "", "href": "https://b.example", "body": ""},
    ]


def test_google_returns_empty_list_on_non_dict_json():
    g = _searcher()
    resp = MagicMock(status_code=200, text='[]')
    with patch(
        "gpt_researcher.retrievers.google.google.requests.get", return_value=resp
    ), patch(
        "gpt_researcher.retrievers.google.google.json.loads", return_value=[]
    ):
        assert g.search() == []
