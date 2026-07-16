"""SearchApiSearch must tolerate partial / non-list organic payloads."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.searchapi.searchapi import SearchApiSearch


def _search_with_payload(payload):
    with patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test-key"}):
        retriever = SearchApiSearch("q")
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    with patch("gpt_researcher.retrievers.searchapi.searchapi.requests.get", return_value=resp):
        return retriever.search(max_results=5)


def test_searchapi_skips_results_missing_keys():
    out = _search_with_payload(
        {
            "organic_results": [
                {"title": "Good", "link": "https://ok.example", "snippet": "s"},
                {"title": "No link"},  # missing link
                "not-a-dict",
            ]
        }
    )
    assert out == [
        {"title": "Good", "href": "https://ok.example", "body": "s"},
    ]


def test_searchapi_no_organic_results_returns_empty():
    assert _search_with_payload({"search_metadata": {}}) == []


def test_searchapi_null_organic_results_returns_empty():
    assert _search_with_payload({"organic_results": None}) == []


def test_searchapi_skips_youtube_links():
    out = _search_with_payload(
        {
            "organic_results": [
                {"title": "yt", "link": "https://www.youtube.com/watch?v=1", "snippet": "x"},
                {"title": "Good", "link": "https://ok.example", "snippet": "s"},
            ]
        }
    )
    assert out == [{"title": "Good", "href": "https://ok.example", "body": "s"}]
