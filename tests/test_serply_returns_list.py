"""Regression test: Serply retrievers' search must always return a list, never None.

Sibling retrievers (serper/serpapi/brave/bing) return [] on error; callers
(`get_search_results` -> `len(search_results)`) crash on None.
"""

import os
import sys
import types
from unittest.mock import patch

# The retrievers only import os, urllib, requests. Stub requests so import works
# without the dependency and so we can drive the error paths deterministically.
if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")

from gpt_researcher.retrievers.serply.serply import SerplySearch  # noqa: E402
from gpt_researcher.retrievers.serply_scholar.serply_scholar import (  # noqa: E402
    SerplyScholarSearch,
)


class _Resp:
    def __init__(self, payload, raises=False):
        self._payload = payload
        self._raises = raises

    def json(self):
        if self._raises:
            raise ValueError("not json")
        return self._payload


def _web():
    os.environ["SERPLY_API_KEY"] = "test-key"
    return SerplySearch("hello world")


def _scholar():
    os.environ["SERPLY_API_KEY"] = "test-key"
    return SerplyScholarSearch("hello world")


def test_web_returns_list_when_response_none():
    with patch("gpt_researcher.retrievers.serply.serply.requests.get", return_value=None):
        out = _web().search()
    assert out == []
    assert len(out) == 0  # would TypeError if None


def test_web_returns_list_when_body_unparseable():
    with patch(
        "gpt_researcher.retrievers.serply.serply.requests.get",
        return_value=_Resp(None, raises=True),
    ):
        assert _web().search() == []


def test_web_returns_list_when_json_null():
    with patch(
        "gpt_researcher.retrievers.serply.serply.requests.get",
        return_value=_Resp(None),
    ):
        assert _web().search() == []


def test_scholar_returns_list_when_response_none():
    with patch(
        "gpt_researcher.retrievers.serply_scholar.serply_scholar.requests.get",
        return_value=None,
    ):
        out = _scholar().search()
    assert out == []
    assert len(out) == 0


def test_scholar_returns_list_when_articles_missing():
    with patch(
        "gpt_researcher.retrievers.serply_scholar.serply_scholar.requests.get",
        return_value=_Resp({"something_else": []}),
    ):
        assert _scholar().search() == []
