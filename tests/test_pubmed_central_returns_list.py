"""Regression test: PubMedCentralSearch.search must return [] (never None).

Callers (actions.query_processing.get_search_results -> List[Dict]) and
skills.researcher (`len(search_results)`) crash on None.
"""

import sys
import types
from unittest.mock import patch

if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")

from gpt_researcher.retrievers.pubmed_central.pubmed_central import (  # noqa: E402
    PubMedCentralSearch,
)


def test_search_returns_list_when_no_article_ids():
    s = PubMedCentralSearch("cancer")
    with patch.object(PubMedCentralSearch, "_search_articles", return_value=None):
        out = s.search()
    assert out == []
    assert len(out) == 0  # would TypeError if None


def test_search_returns_list_when_empty_article_ids():
    s = PubMedCentralSearch("cancer")
    with patch.object(PubMedCentralSearch, "_search_articles", return_value=[]):
        out = s.search()
    assert out == []


def test_search_articles_malformed_esearchresult_returns_empty_list():
    s = PubMedCentralSearch("cancer")
    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"esearchresult": None}

    with patch(
        "gpt_researcher.retrievers.pubmed_central.pubmed_central.requests.get",
        return_value=Resp(),
    ):
        out = s._search_articles(max_results=5)
    assert out == []


def test_search_articles_non_list_idlist_returns_empty_list():
    s = PubMedCentralSearch("cancer")
    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"esearchresult": {"idlist": "1,2,3"}}

    with patch(
        "gpt_researcher.retrievers.pubmed_central.pubmed_central.requests.get",
        return_value=Resp(),
    ):
        out = s._search_articles(max_results=5)
    assert out == []
