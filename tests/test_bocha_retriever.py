"""Guards for BoChaSearch malformed payloads."""
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.bocha.bocha import BoChaSearch


def _resp(payload, status=200):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    r.raise_for_status.return_value = None
    return r


@patch.dict("os.environ", {"BOCHA_API_KEY": "k"}, clear=False)
@patch("gpt_researcher.retrievers.bocha.bocha.requests.post")
def test_bocha_skips_malformed_items(mock_post):
    mock_post.return_value = _resp(
        {
            "data": {
                "webPages": {
                    "value": [
                        None,
                        {"name": "n"},
                        {
                            "name": "ok",
                            "url": "https://example.com",
                            "snippet": "snip",
                        },
                    ]
                }
            }
        }
    )
    out = BoChaSearch("q").search()
    assert out == [
        {"title": "ok", "href": "https://example.com", "body": "snip"}
    ]


@patch.dict("os.environ", {"BOCHA_API_KEY": "k"}, clear=False)
@patch("gpt_researcher.retrievers.bocha.bocha.requests.post")
def test_bocha_bad_envelope_returns_empty(mock_post):
    mock_post.return_value = _resp({"data": {}})
    assert BoChaSearch("q").search() == []
