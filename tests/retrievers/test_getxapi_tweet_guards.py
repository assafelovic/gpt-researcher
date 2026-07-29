"""GetXAPI tweet list / author shape guards."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
MOD_PATH = ROOT / "gpt_researcher" / "retrievers" / "getxapi" / "getxapi.py"


def _load():
    name = "gptr_getxapi_under_test"
    spec = importlib.util.spec_from_file_location(name, MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_skips_bad_tweets_and_bad_author():
    mod = _load()
    payload = {
        "tweets": [
            "x",
            {"author": "anon", "text": "hi", "id": "1", "username": "u1"},
            {
                "author": {"userName": "alice"},
                "text": "hello world",
                "id": "2",
                "likeCount": 3,
            },
        ]
    }
    with patch.dict("os.environ", {"GETXAPI_API_KEY": "k"}):
        r = mod.GetXAPISearch("q")
    with patch.object(mod.urllib.request, "urlopen", return_value=_Resp(payload)):
        out = r._search_tweets(max_results=10)
    assert len(out) == 2
    assert out[0]["href"] == "https://x.com/u1/status/1"
    assert out[1]["href"] == "https://x.com/alice/status/2"


def test_non_list_tweets_empty():
    mod = _load()
    with patch.dict("os.environ", {"GETXAPI_API_KEY": "k"}):
        r = mod.GetXAPISearch("q")
    with patch.object(mod.urllib.request, "urlopen", return_value=_Resp({"tweets": {"id": 1}})):
        assert r._search_tweets(5) == []
