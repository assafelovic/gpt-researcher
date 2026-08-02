"""Google CSE items shape guards."""

import json
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.google.google import GoogleSearch


def _run(payload, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.text = json.dumps(payload) if not isinstance(payload, str) else payload
    with patch.dict(
        "os.environ",
        {"GOOGLE_API_KEY": "k", "GOOGLE_CX_KEY": "cx"},
        clear=False,
    ):
        # Some installs use different env names — patch get_api_key/get_cxe
        with patch.object(GoogleSearch, "get_api_key", return_value="k"), patch.object(
            GoogleSearch, "get_cx_key", return_value="cx"
        ), patch(
            "gpt_researcher.retrievers.google.google.requests.get", return_value=resp
        ):
            return GoogleSearch("q").search(max_results=5)


def test_skips_non_dict_items_and_youtube():
    out = _run(
        {
            "items": [
                None,
                "x",
                {"link": "https://youtube.com/watch?v=1", "title": "yt"},
                {
                    "link": "https://example.com/a",
                    "title": "A",
                    "snippet": "body",
                },
            ]
        }
    )
    assert out == [
        {"title": "A", "href": "https://example.com/a", "body": "body"}
    ]


def test_items_not_list_returns_empty():
    assert _run({"items": {"not": "list"}}) == []
