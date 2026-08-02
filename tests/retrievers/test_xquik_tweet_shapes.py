"""Xquik retriever should tolerate non-dict tweets and payload shapes."""

import json
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.xquik.xquik import XquikSearch


def _run(payload):
    raw = json.dumps(payload).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = raw
    cm.__exit__.return_value = False
    with patch.dict("os.environ", {"XQUIK_API_KEY": "k"}):
        with patch(
            "gpt_researcher.retrievers.xquik.xquik.urllib.request.urlopen",
            return_value=cm,
        ):
            return XquikSearch("hello").search(max_results=5)


def test_skips_non_dict_tweets_and_empty_ids():
    out = _run(
        {
            "tweets": [
                None,
                "x",
                {"text": "no id"},
                {
                    "id": "1",
                    "text": "hi",
                    "author": {"username": "alice"},
                    "likeCount": 2,
                },
            ]
        }
    )
    assert len(out) == 1
    assert out[0]["href"].endswith("/status/1")
    assert "hi" in out[0]["body"]


def test_non_list_tweets_returns_empty():
    assert _run({"tweets": {"bad": True}}) == []


def test_non_dict_root_returns_empty():
    assert _run([1, 2, 3]) == []
