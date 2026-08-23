"""ArxivSearch must tolerate incomplete Result objects and API errors.

Bare attribute access on title/pdf_url/summary blew up (or produced href=None)
when arxiv returned partial metadata, and network/API exceptions crashed the
whole retriever rather than returning [].
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock


# Lightweight arxiv stub for pure unit tests (no network, no arxiv install).
_arxiv = types.ModuleType("arxiv")


class _SortCriterion:
    SubmittedDate = "SubmittedDate"
    Relevance = "Relevance"


_arxiv.SortCriterion = _SortCriterion


class _Client:
    def __init__(self):
        self._results = []

    def results(self, search):
        return list(self._results)


_arxiv.Client = _Client
_arxiv.Search = MagicMock
sys.modules["arxiv"] = _arxiv

path = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "arxiv"
    / "arxiv.py"
)
spec = importlib.util.spec_from_file_location("_arxiv_ut", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ArxivSearch = mod.ArxivSearch


def test_skips_results_without_href_and_defaults_fields():
    client = _arxiv.Client()
    client._results = [
        SimpleNamespace(title="A", pdf_url="https://arxiv.org/pdf/1", summary="s1"),
        SimpleNamespace(title="B", pdf_url=None, entry_id=None, summary="s2"),
        SimpleNamespace(title=None, pdf_url="https://arxiv.org/pdf/3", summary=None),
        SimpleNamespace(title="D", pdf_url=None, entry_id="https://arxiv.org/abs/4", summary="s4"),
    ]
    _arxiv.Client = lambda: client
    out = ArxivSearch("q").search()
    assert out == [
        {"title": "A", "href": "https://arxiv.org/pdf/1", "body": "s1"},
        {"title": "", "href": "https://arxiv.org/pdf/3", "body": ""},
        {"title": "D", "href": "https://arxiv.org/abs/4", "body": "s4"},
    ]


def test_api_exception_returns_empty():
    class BoomClient:
        def results(self, search):
            raise RuntimeError("network down")

    _arxiv.Client = BoomClient
    assert ArxivSearch("q").search() == []
