"""fastCRW data[] rows may not all be dicts."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MOD_PATH = ROOT / "gpt_researcher" / "retrievers" / "crw" / "crw.py"


def _load():
    name = "gptr_crw_under_test"
    spec = importlib.util.spec_from_file_location(name, MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_search_skips_non_dict_and_keeps_valid():
    mod = _load()
    payload = {
        "success": True,
        "data": [
            "bad",
            None,
            {"description": "no url"},
            {"url": "https://example.com", "markdown": "body"},
        ],
    }
    with patch.dict("os.environ", {"CRW_API_KEY": "k"}, clear=False):
        r = mod.CRWRetriever("q")
    with patch.object(r, "_search", return_value=payload):
        out = r.search(max_results=10)
    assert out == [{"href": "https://example.com", "body": "body"}]


def test_search_non_list_data_returns_empty_not_crash():
    mod = _load()
    with patch.dict("os.environ", {"CRW_API_KEY": "k"}, clear=False):
        r = mod.CRWRetriever("q")
    with patch.object(r, "_search", return_value={"success": True, "data": {"url": "x"}}):
        out = r.search(max_results=10)
    assert out == []
