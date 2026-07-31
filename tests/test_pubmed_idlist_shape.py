"""PubMed esearch idlist must be a list before search loops."""
import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock

_requests = types.ModuleType("requests")
_requests.get = MagicMock()
_requests.RequestException = Exception
sys.modules["requests"] = _requests

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "pubmed_central"
    / "pubmed_central.py"
)
_spec = importlib.util.spec_from_file_location("_pubmed_idlist", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_non_list_idlist_returns_empty():
    s = _mod.PubMedCentralSearch("q")
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"esearchresult": {"idlist": "PMC1"}}
    _mod.requests.get = MagicMock(return_value=resp)
    assert s._search_articles(5) == []


def test_list_ids_normalized_to_str():
    s = _mod.PubMedCentralSearch("q")
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"esearchresult": {"idlist": [1, "PMC2", None, {}]}}
    _mod.requests.get = MagicMock(return_value=resp)
    assert s._search_articles(5) == ["1", "PMC2"]
