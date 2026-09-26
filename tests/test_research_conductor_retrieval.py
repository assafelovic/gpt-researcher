import unittest
from types import SimpleNamespace

from gpt_researcher.skills.researcher import ResearchConductor


class FakeSnippetRetriever:
    def __init__(self, query, query_domains=None):
        self.query = query
        self.query_domains = query_domains or []

    def search(self, max_results=10):
        return [
            {
                "href": "https://example.com/one",
                "body": "A" * 180,
            },
            {
                "href": "https://example.com/two",
                "body": "B" * 220,
            },
        ]


class FakeFullContentRetriever:
    def __init__(self, query, query_domains=None):
        self.query = query
        self.query_domains = query_domains or []

    def search(self, max_results=10):
        return [
            {
                "href": "https://example.com/full",
                "body": "short summary",
                "raw_content": "C" * 500,
            }
        ]


class ResearchConductorRetrievalTests(unittest.IsolatedAsyncioTestCase):
    def make_researcher(self, retriever_class):
        class FakeResearcher:
            def __init__(self):
                self.retrievers = [retriever_class]
                self.cfg = SimpleNamespace(max_search_results_per_query=5)
                self.verbose = False
                self.websocket = None
                self.visited_urls = set()
                self.research_sources = []

            def add_research_sources(self, sources):
                self.research_sources.extend(sources)

        return FakeResearcher()

    async def test_snippet_only_results_are_sent_to_scraper(self):
        researcher = self.make_researcher(FakeSnippetRetriever)
        conductor = ResearchConductor(researcher)

        urls, prefetched = await conductor._search_relevant_source_urls("rust async runtimes")

        self.assertCountEqual(
            urls,
            ["https://example.com/one", "https://example.com/two"],
        )
        self.assertEqual(prefetched, [])

    async def test_raw_content_results_stay_prefetched(self):
        researcher = self.make_researcher(FakeFullContentRetriever)
        conductor = ResearchConductor(researcher)

        urls, prefetched = await conductor._search_relevant_source_urls("pubmed article")

        self.assertEqual(urls, [])
        self.assertEqual(
            prefetched,
            [{"url": "https://example.com/full", "raw_content": "C" * 500}],
        )


class FakeDeclaredPrefetchRetriever:
    """Retriever that fetches content itself (no scraping needed)."""

    requires_scraping = False

    def __init__(self, query, query_domains=None):
        self.query = query
        self.query_domains = query_domains or []

    def search(self, max_results=10):
        return [
            {
                "href": "https://example.com/prefetched",
                "raw_content": "D" * 500,
            }
        ]


class ResearchConductorVisitedUrlsTests(unittest.IsolatedAsyncioTestCase):
    """#2100: prefetched URLs must join visited_urls like scraped ones do."""

    def make_researcher(self, retriever_class):
        class FakeResearcher:
            def __init__(self):
                self.retrievers = [retriever_class]
                self.cfg = SimpleNamespace(max_search_results_per_query=5)
                self.verbose = False
                self.websocket = None
                self.visited_urls = set()
                self.research_sources = []

            def add_research_sources(self, sources):
                self.research_sources.extend(sources)

        return FakeResearcher()

    async def test_declared_prefetch_marks_visited(self):
        researcher = self.make_researcher(FakeDeclaredPrefetchRetriever)
        conductor = ResearchConductor(researcher)

        await conductor._search_relevant_source_urls("sub-query one")
        _, prefetched = await conductor._search_relevant_source_urls("sub-query two")

        self.assertEqual(researcher.visited_urls, {"https://example.com/prefetched"})
        self.assertEqual(len(prefetched), 1)

    async def test_legacy_heuristic_prefetch_marks_visited(self):
        researcher = self.make_researcher(FakeFullContentRetriever)
        conductor = ResearchConductor(researcher)

        await conductor._search_relevant_source_urls("pubmed article")

        self.assertEqual(researcher.visited_urls, {"https://example.com/full"})


if __name__ == "__main__":
    unittest.main()
