"""BraveSearch must tolerate non-dict web/results payloads."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.brave.brave import BraveSearch


def _search(payload):
    with patch.dict("os.environ", {"BRAVE_API_KEY": "k"}):
        r = BraveSearch("q")
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    with patch("gpt_researcher.retrievers.brave.brave.requests.get", return_value=resp):
        return r.search(max_results=5)


def test_brave_skips_non_dict_rows():
    out = _search(
        {
            "web": {
                "results": [
                    {"title": "G", "url": "https://ok.example", "description": "d"},
                    "bad",
                    {"title": "n", "description": "d"},
                ]
            }
        }
    )
    assert out == [{"title": "G", "href": "https://ok.example", "body": "d"}]


def test_brave_null_web_returns_empty():
    assert _search({"web": None}) == []


def test_brave_non_list_results_returns_empty():
    assert _search({"web": {"results": {"x": 1}}}) == []
