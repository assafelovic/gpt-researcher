"""GetXAPISearch must skip non-dict tweets and guard non-list payloads."""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock, patch


path = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "getxapi"
    / "getxapi.py"
)
# Ensure no network
spec = importlib.util.spec_from_file_location("_getxapi_ut", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
GetXAPISearch = mod.GetXAPISearch


def test_skips_non_dict_tweets_and_null_author():
    payload = {
        "tweets": [
            {
                "author": {"userName": "alice"},
                "text": "hello",
                "id": "1",
            },
            "bad",
            {
                "author": None,
                "text": "no author",
                "id": "2",
            },
        ]
    }

    with patch.dict("os.environ", {"GETXAPI_API_KEY": "k"}):
        inst = GetXAPISearch("q")
        with patch.object(inst, "_search_tweets", wraps=inst._search_tweets):
            # patch json load path inside _search_tweets
            class CM:
                def __enter__(self):
                    resp = MagicMock()
                    resp.read.return_value = b""
                    return resp

                def __exit__(self, *a):
                    return False

            import json as _json

            class FakeResp:
                def read(self):
                    return _json.dumps(payload).encode()

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

            with patch.object(mod.urllib.request, "urlopen", return_value=FakeResp()):
                out = inst.search(max_results=10)

    assert len(out) == 2
    assert out[0]["title"].startswith("@alice:")
    assert out[1]["title"].startswith("@unknown:")
    assert all("href" in r for r in out)


def test_non_list_tweets_returns_empty():
    class FakeResp:
        def read(self):
            return b'{"tweets": {"nope": true}}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch.dict("os.environ", {"GETXAPI_API_KEY": "k"}):
        inst = GetXAPISearch("q")
        with patch.object(mod.urllib.request, "urlopen", return_value=FakeResp()):
            assert inst.search() == []
