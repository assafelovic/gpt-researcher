"""Regression test: SerperSearch.search must always return a list, never None.

Sibling retrievers (serpapi/brave/bing/searx) return [] on error; callers
(`get_search_results` -> `len(search_results)`) crash on None.
"""

from unittest.mock import patch

from gpt_researcher.retrievers.serper.serper import SerperSearch


def _make(monkeypatch_env):
    import os

    os.environ["SERPER_API_KEY"] = "test-key"
    return SerperSearch("hello world")


def test_search_returns_list_when_response_none():
    s = _make(None)
    with patch(
        "gpt_researcher.retrievers.serper.serper.requests.request",
        return_value=None,
    ):
        out = s.search()
    assert out == []
    assert len(out) == 0  # would TypeError if None


def test_search_returns_list_when_body_unparseable():
    s = _make(None)

    class _Resp:
        text = "<<not json>>"

    with patch(
        "gpt_researcher.retrievers.serper.serper.requests.request",
        return_value=_Resp(),
    ):
        out = s.search()
    assert out == []


def test_search_returns_list_when_json_null():
    s = _make(None)

    class _Resp:
        text = "null"

    with patch(
        "gpt_researcher.retrievers.serper.serper.requests.request",
        return_value=_Resp(),
    ):
        out = s.search()
    assert out == []
