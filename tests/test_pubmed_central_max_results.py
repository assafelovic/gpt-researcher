"""Unit tests for PubMedCentralSearch max_results guards and bounding."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from unittest.mock import patch

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PATH = _ROOT / "gpt_researcher" / "retrievers" / "pubmed_central" / "pubmed_central.py"

_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.retrievers.pubmed_central.pubmed_central_under_test",
    _PATH,
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["gpt_researcher.retrievers.pubmed_central.pubmed_central_under_test"] = _mod
_spec.loader.exec_module(_mod)

PubMedCentralSearch = _mod.PubMedCentralSearch


def test_non_positive_max_results_returns_empty_without_request():
    searcher = PubMedCentralSearch("oncology")
    with patch("requests.get") as mock_get:
        assert searcher.search(max_results=0) == []
        assert searcher.search(max_results=-1) == []
        assert searcher.search(max_results=-10) == []
        mock_get.assert_not_called()


def test_search_articles_non_positive_returns_empty_without_request():
    searcher = PubMedCentralSearch("immunology")
    with patch("requests.get") as mock_get:
        assert searcher._search_articles(max_results=0) == []
        assert searcher._search_articles(max_results=-1) == []
        mock_get.assert_not_called()


def test_bounds_results_to_max_results():
    searcher = PubMedCentralSearch("genomics")
    article_ids = ["PMC1", "PMC2", "PMC3", "PMC4", "PMC5"]

    def fake_fetch(article_id):
        return {
            "href": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{article_id}/",
            "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{article_id}/",
            "body": f"Body for {article_id}",
            "raw_content": f"Body for {article_id}",
            "title": f"Title {article_id}",
        }

    with (
        patch.object(searcher, "_search_articles", return_value=article_ids),
        patch.object(searcher, "_fetch_full_text", side_effect=fake_fetch),
    ):
        results = searcher.search(max_results=2)
        assert len(results) == 2
        assert results[0]["title"] == "Title PMC1"
        assert results[1]["title"] == "Title PMC2"


def test_query_domains_stored():
    searcher_domains = PubMedCentralSearch("cancer", query_domains=["nih.gov"])
    assert searcher_domains.query_domains == ["nih.gov"]

    searcher_none = PubMedCentralSearch("cancer")
    assert searcher_none.query_domains is None

    searcher_empty = PubMedCentralSearch("cancer", query_domains=[])
    assert searcher_empty.query_domains is None
