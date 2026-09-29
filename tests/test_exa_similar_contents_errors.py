"""ExaSearch.find_similar and get_contents must swallow client failures and
None / non-list results instead of raising — mirroring the search() guards."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from gpt_researcher.retrievers.exa.exa import ExaSearch


def _searcher():
    # bypass __init__ pkg/API setup
    s = ExaSearch.__new__(ExaSearch)
    s.query = "q"
    s.query_domains = None
    s.api_key = "k"
    s.client = MagicMock()
    return s


def test_find_similar_swallows_client_errors():
    s = _searcher()

    class Boom:
        def find_similar(self, *a, **k):
            raise RuntimeError("api down")

    s.client = Boom()
    assert s.find_similar("https://seed") == []


def test_find_similar_tolerates_none_results():
    s = _searcher()
    s.client.find_similar.return_value = None
    assert s.find_similar("https://seed") == []


def test_find_similar_tolerates_non_list_results():
    s = _searcher()
    s.client.find_similar.return_value = SimpleNamespace(results="oops")
    assert s.find_similar("https://seed") == []


def test_get_contents_swallows_client_errors():
    s = _searcher()

    class Boom:
        def get_contents(self, *a, **k):
            raise RuntimeError("api down")

    s.client = Boom()
    assert s.get_contents(["1"]) == []


def test_get_contents_tolerates_none_results():
    s = _searcher()
    s.client.get_contents.return_value = None
    assert s.get_contents(["1"]) == []


def test_get_contents_tolerates_non_list_results():
    s = _searcher()
    s.client.get_contents.return_value = SimpleNamespace(results="oops")
    assert s.get_contents(["1"]) == []