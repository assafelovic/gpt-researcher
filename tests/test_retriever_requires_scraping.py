"""Retrievers declare whether their results still need scraping (#1846, #1892).

`_search_relevant_source_urls` used to infer this from the length of any
`raw_content` field -- anything over 100 characters was assumed to be an
already-fetched page. A search snippet longer than that was therefore treated
as article text, its URL was never scraped, and the report carried no
verifiable citation for it.

`BaseRetriever.requires_scraping` replaces the guess with a declaration. The
legacy heuristic is kept for retrievers that do not declare, so third-party and
user-defined retrievers behave exactly as before.
"""
import asyncio
import types

import pytest

from gpt_researcher.retrievers.base import BaseRetriever
from gpt_researcher.skills.researcher import ResearchConductor

LONG_SNIPPET = "a plausible search snippet " * 20  # >100 chars, but only a snippet


def _conductor(retriever_classes):
    researcher = types.SimpleNamespace(
        retrievers=retriever_classes,
        cfg=types.SimpleNamespace(max_search_results_per_query=5),
        add_research_sources=lambda *a, **k: None,
        visited_urls=set(),
        verbose=False,
        websocket=None,
    )
    c = ResearchConductor(researcher)
    c.logger = types.SimpleNamespace(
        info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None
    )
    # _get_new_urls dedupes against researcher state; identity keeps tests focused.
    c._get_new_urls = lambda urls: asyncio.sleep(0, result=urls)
    return c


def _make(name, results, **attrs):
    def __init__(self, query, query_domains=None, **kw):
        pass

    def search(self, max_results=7):
        return results

    return type(name, (), {"__init__": __init__, "search": search, **attrs})


def _run(conductor):
    return asyncio.run(conductor._search_relevant_source_urls("q"))


def test_declared_scraping_keeps_long_snippets_scrapeable():
    """The #1846 / #1892 regression: a >100 char snippet must not suppress scraping."""
    R = _make("SnippetRetriever",
              [{"url": "https://example.com/a", "raw_content": LONG_SNIPPET}],
              requires_scraping=True)
    urls, prefetched = _run(_conductor([R]))
    assert urls == ["https://example.com/a"]
    assert prefetched == []


def test_declared_content_is_used_without_scraping():
    R = _make("FullTextRetriever",
              [{"url": "https://example.com/b", "raw_content": "real article text"}],
              requires_scraping=False)
    urls, prefetched = _run(_conductor([R]))
    assert urls == []
    assert prefetched == [{"url": "https://example.com/b", "raw_content": "real article text"}]


def test_declared_content_falls_back_to_scraping_when_empty():
    """requires_scraping=False but no content on this row -- still worth fetching."""
    R = _make("PartialRetriever", [{"url": "https://example.com/c"}], requires_scraping=False)
    urls, prefetched = _run(_conductor([R]))
    assert urls == ["https://example.com/c"]
    assert prefetched == []


def test_undeclared_retriever_keeps_legacy_behaviour():
    """Third-party retrievers must be unaffected: >100 chars still means content."""
    R = _make("LegacyRetriever",
              [{"url": "https://example.com/d", "raw_content": LONG_SNIPPET}])
    urls, prefetched = _run(_conductor([R]))
    assert urls == []
    assert prefetched and prefetched[0]["url"] == "https://example.com/d"


def test_undeclared_short_content_still_scrapes():
    R = _make("LegacyShort", [{"url": "https://example.com/e", "raw_content": "tiny"}])
    urls, prefetched = _run(_conductor([R]))
    assert urls == ["https://example.com/e"]
    assert prefetched == []


def test_rows_without_a_url_are_skipped():
    R = _make("NoUrl", [{"raw_content": LONG_SNIPPET}, {"url": "https://example.com/f"}],
              requires_scraping=True)
    urls, prefetched = _run(_conductor([R]))
    assert urls == ["https://example.com/f"]
    assert prefetched == []


def test_base_class_defaults_to_requiring_scraping():
    assert BaseRetriever.requires_scraping is True


def test_base_class_requires_a_search_method():
    with pytest.raises(TypeError):
        BaseRetriever()  # abstract: search() is not implemented


@pytest.mark.parametrize(
    "import_path, cls_name, expected",
    [
        ("gpt_researcher.retrievers.tavily.tavily_search", "TavilySearch", True),
        ("gpt_researcher.retrievers.searx.searx", "SearxSearch", True),
        ("gpt_researcher.retrievers.duckduckgo.duckduckgo", "Duckduckgo", True),
        ("gpt_researcher.retrievers.nimble.nimble_search", "NimbleSearch", True),
        ("gpt_researcher.retrievers.pubmed_central.pubmed_central", "PubMedCentralSearch", False),
        ("gpt_researcher.retrievers.custom.custom", "CustomRetriever", False),
    ],
)
def test_shipped_declarations(import_path, cls_name, expected):
    import importlib
    cls = getattr(importlib.import_module(import_path), cls_name)
    assert cls.requires_scraping is expected
