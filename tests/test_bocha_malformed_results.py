"""BoChaSearch must skip non-dict / href-less organic hits."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.bocha.bocha import BoChaSearch


def _search(payload):
    with patch.dict("os.environ", {"BOCHA_API_KEY": "k"}):
        r = BoChaSearch("q")
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    with patch("gpt_researcher.retrievers.bocha.bocha.requests.post", return_value=resp):
        return r.search(max_results=5)


def test_bocha_skips_non_dict_and_missing_url():
    out = _search(
        {
            "data": {
                "webPages": {
                    "value": [
                        {"name": "Good", "url": "https://ok.example", "snippet": "s"},
                        "x",
                        {"name": "NoURL", "snippet": "s"},
                    ]
                }
            }
        }
    )
    assert out == [{"title": "Good", "href": "https://ok.example", "body": "s"}]


def test_bocha_non_list_value_returns_empty():
    assert _search({"data": {"webPages": {"value": {"not": "list"}}}}) == []
