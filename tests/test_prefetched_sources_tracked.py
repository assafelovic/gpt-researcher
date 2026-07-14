"""Regression tests: prefetched full-text sources (retrievers that already
return raw_content, e.g. PubMed Central or Tavily with include_raw_content)
must be tracked in visited_urls, exactly like scraped URLs.

Their content is merged into the research context (_scrape_data_by_urls:
`scraped_content.extend(prefetched_content)`), so they must be:
  1. recorded in visited_urls, which drives get_source_urls() and the report's
     references (add_references(report, visited_urls)); and
  2. deduped across sub-queries, so an article that matches several related
     sub-queries is not merged into the context (and billed) more than once.

Before the fix, prefetched URLs went only into research_sources, never
visited_urls, so they were omitted from references and re-collected every
sub-query while scraped URLs were correctly deduped.
"""
import asyncio
import types

from gpt_researcher.skills.researcher import ResearchConductor

PREFETCH_URL = "https://pmc.example.org/article/PMC123"
SCRAPE_URL = "https://blog.example.org/post"


class _FakeRetriever:
    """Returns the same prefetched (raw_content) result + bare-url result for
    every sub-query, modelling an article that matches related sub-queries."""

    def __init__(self, query, query_domains=None):
        self.query = query

    def search(self, max_results=5):
        return [
            {"href": PREFETCH_URL, "raw_content": "F" * 500},
            {"href": SCRAPE_URL, "body": "short snippet"},
        ]


def _make_researcher():
    r = types.SimpleNamespace()
    r.retrievers = [_FakeRetriever]
    r.cfg = types.SimpleNamespace(max_search_results_per_query=5)
    r.visited_urls = set()
    r.research_sources = []
    r.add_research_sources = lambda sources: r.research_sources.extend(sources)
    r.get_source_urls = lambda: list(r.visited_urls)
    r.verbose = False
    r.websocket = None
    r.vector_store = None

    async def browse_urls(urls):
        return [{"url": u, "raw_content": "scraped body"} for u in urls]

    r.scraper_manager = types.SimpleNamespace(browse_urls=browse_urls)
    return r


def test_prefetched_source_is_recorded_in_visited_urls():
    r = _make_researcher()
    conductor = ResearchConductor(r)

    asyncio.run(conductor._scrape_data_by_urls("sub query 1"))

    # The prefetched full-text source contributes content, so it must appear in
    # the source/reference list, not only the scraped URL.
    assert PREFETCH_URL in r.visited_urls
    assert PREFETCH_URL in r.get_source_urls()
    assert SCRAPE_URL in r.visited_urls


def test_prefetched_source_deduped_across_sub_queries():
    r = _make_researcher()
    conductor = ResearchConductor(r)

    sq1 = asyncio.run(conductor._scrape_data_by_urls("sub query 1"))
    sq2 = asyncio.run(conductor._scrape_data_by_urls("sub query 2"))

    context_urls = [d["url"] for d in sq1 + sq2]
    # The same prefetched article must be merged into the context exactly once,
    # matching the dedup the scraped path already gets via visited_urls.
    assert context_urls.count(PREFETCH_URL) == 1
    assert context_urls.count(SCRAPE_URL) == 1
