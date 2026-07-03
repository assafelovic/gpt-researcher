"""Regression tests for snippet-vs-prefetched-content classification.

Snippet retrievers (e.g. searx) return short search-result snippets under
the ``body`` key -- searx maps SearXNG's ``content`` field to ``body``.
These snippets are typically 150-400 chars.

``_search_relevant_source_urls`` used to treat any result with
``raw_content`` OR ``body`` longer than 100 chars as *prefetched full
content* and skip scraping entirely. Because snippets easily exceed 100
chars, virtually every snippet-retriever result was mistaken for full page
content, so the scraper was essentially never invoked and report quality
collapsed (see issue #1846).

The fix keys prefetched-content detection on ``raw_content`` only, so
``body`` snippets flow through to real scraping while genuine full-text
pass-through (pubmed_central, tavily-with-raw-content) is unchanged.
"""

import asyncio
import unittest

from gpt_researcher.skills.researcher import ResearchConductor


class _FakeRetriever:
    """Minimal retriever returning a fixed result set."""

    _results = []

    def __init__(self, query, query_domains=None):
        self.query = query

    def search(self, max_results=5):
        return type(self)._results


class _FakeResearcher:
    """Minimal researcher stub for ResearchConductor."""

    def __init__(self, retriever_cls):
        self.retrievers = [retriever_cls]
        self.visited_urls = set()
        self.verbose = False
        self.websocket = None
        self.research_sources = []

        class _Cfg:
            max_search_results_per_query = 5

        self.cfg = _Cfg()

    def add_research_sources(self, sources):
        self.research_sources.extend(sources)


def _run(retriever_cls):
    researcher = _FakeResearcher(retriever_cls)
    conductor = ResearchConductor(researcher)
    return researcher, asyncio.run(
        conductor._search_relevant_source_urls("q")
    )


class TestSnippetScraping(unittest.TestCase):
    def test_body_snippet_flows_to_scraping(self):
        """A >100-char ``body`` snippet must NOT be treated as prefetched."""
        snippet = "x" * 250  # realistic snippet length, passes the old >100 guard

        class R(_FakeRetriever):
            _results = [{"href": "https://example.com/a", "body": snippet}]

        researcher, (new_urls, prefetched) = _run(R)
        self.assertEqual(new_urls, ["https://example.com/a"])
        self.assertEqual(prefetched, [])
        self.assertEqual(researcher.research_sources, [])

    def test_raw_content_still_prefetched(self):
        """Genuine ``raw_content`` full text is still passed through."""
        full = "y" * 2000

        class R(_FakeRetriever):
            _results = [{"url": "https://pmc.example.com/b", "raw_content": full}]

        researcher, (new_urls, prefetched) = _run(R)
        self.assertEqual(new_urls, [])
        self.assertEqual(len(prefetched), 1)
        self.assertEqual(prefetched[0]["url"], "https://pmc.example.com/b")
        self.assertEqual(prefetched[0]["raw_content"], full)
        self.assertEqual(researcher.research_sources, [{"url": "https://pmc.example.com/b"}])


if __name__ == "__main__":
    unittest.main()
