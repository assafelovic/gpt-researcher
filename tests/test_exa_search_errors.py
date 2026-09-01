"""ExaSearch.search must return [] on API failures, not raise."""

from types import SimpleNamespace

from gpt_researcher.retrievers.exa.exa import ExaSearch


def test_search_swallows_client_errors(monkeypatch):
    searcher = ExaSearch.__new__(ExaSearch)
    searcher.query = "q"
    searcher.query_domains = None

    class Boom:
        def search(self, *a, **k):
            raise RuntimeError("api down")

    searcher.client = Boom()
    assert searcher.search() == []


def test_search_tolerates_missing_results_list():
    searcher = ExaSearch.__new__(ExaSearch)
    searcher.query = "q"
    searcher.query_domains = None

    class Ok:
        def search(self, *a, **k):
            return SimpleNamespace(results=None)

    searcher.client = Ok()
    assert searcher.search() == []


def test_search_normalizes_hits():
    searcher = ExaSearch.__new__(ExaSearch)
    searcher.query = "q"
    searcher.query_domains = None

    class Ok:
        def search(self, *a, **k):
            return SimpleNamespace(
                results=[
                    SimpleNamespace(url="https://a.example", text="body", summary=None),
                    SimpleNamespace(url=None, text="x", summary=None),
                    SimpleNamespace(url="https://b.example", text=None, summary="sum"),
                ]
            )

    searcher.client = Ok()
    assert searcher.search() == [
        {"href": "https://a.example", "body": "body"},
        {"href": "https://b.example", "body": "sum"},
    ]
