"""Planning sources must reach retrieval even if later searches return nothing."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from gpt_researcher.skills.researcher import ResearchConductor


class PlanningSourcesTests(unittest.IsolatedAsyncioTestCase):
    def make_conductor(self, *, full_content=False, report_type="research_report"):
        calls = []

        class Retriever:
            requires_scraping = not full_content

            def __init__(self, query, query_domains=None):
                self.query = query

            def search(self, max_results=5):
                calls.append(self.query)
                if len(calls) == 1:
                    result = {"href": "https://example.org/award", "body": "Preview only"}
                    if full_content:
                        result["raw_content"] = "Verified award winner: Example."
                    return [result, dict(result)]
                return []

        async def browse(urls):
            return [{"url": url, "raw_content": "Verified award winner: Example."} for url in urls]

        async def compress(query, data):
            return " ".join(item["raw_content"] for item in data)

        researcher = SimpleNamespace(
            retrievers=[Retriever], cfg=SimpleNamespace(max_search_results_per_query=5),
            verbose=False, websocket=None, visited_urls=set(), role="Researcher",
            parent_query="", report_type=report_type, kwargs={}, add_costs=lambda *a: None,
            add_research_sources=lambda *a: None, vector_store=None,
            scraper_manager=SimpleNamespace(browse_urls=AsyncMock(side_effect=browse)),
            context_manager=SimpleNamespace(get_similar_content_by_query=AsyncMock(side_effect=compress)),
        )
        return ResearchConductor(researcher), calls

    async def run_research(self, conductor, **kwargs):
        with patch("gpt_researcher.skills.researcher.plan_research_outline",
                   AsyncMock(return_value=["targeted follow-up"])), \
             patch("gpt_researcher.skills.researcher.stream_output", AsyncMock()):
            return await conductor._get_context_by_web_search("original question", **kwargs)

    async def test_planning_url_survives_empty_followup_searches(self):
        conductor, calls = self.make_conductor()
        context = await self.run_research(conductor)
        self.assertIn("Verified award winner: Example.", context)
        self.assertNotIn("Preview only", context)
        fetched = [url for call in conductor.researcher.scraper_manager.browse_urls.call_args_list
                   for url in call.args[0]]
        self.assertEqual(fetched.count("https://example.org/award"), 1)
        self.assertIn("targeted follow-up", calls)

    async def test_subtopic_preserves_planning_source_without_researching_original_query(self):
        conductor, calls = self.make_conductor(report_type="subtopic_report")
        context = await self.run_research(conductor)
        self.assertIn("Verified award winner: Example.", context)
        self.assertEqual(calls.count("original question"), 1)

    async def test_full_content_is_preserved_without_fetching_url(self):
        conductor, _ = self.make_conductor(full_content=True)
        context = await self.run_research(conductor)
        self.assertIn("Verified award winner: Example.", context)
        fetched = [url for call in conductor.researcher.scraper_manager.browse_urls.call_args_list
                   for url in call.args[0]]
        self.assertEqual(fetched, [])

    async def test_provided_documents_do_not_trigger_web_scraping(self):
        conductor, _ = self.make_conductor()
        context = await self.run_research(conductor, scraped_data=[
            {"url": "local", "raw_content": "Provided document."}])
        self.assertIn("Provided document.", context)
        conductor.researcher.scraper_manager.browse_urls.assert_not_awaited()

    async def test_failed_initial_page_does_not_abort_followups(self):
        conductor, calls = self.make_conductor()
        conductor.researcher.scraper_manager.browse_urls.side_effect = RuntimeError("Page unavailable")
        await self.run_research(conductor)
        self.assertIn("targeted follow-up", calls)

    async def test_empty_initial_results_still_allow_followup_context(self):
        conductor, _ = self.make_conductor()
        with patch.object(conductor, "_get_initial_search_results", AsyncMock(return_value=[])):
            context = await self.run_research(conductor)
        self.assertIn("Verified award winner: Example.", context)

    async def test_initial_results_do_not_replace_other_retrievers(self):
        conductor, _ = self.make_conductor()

        class OtherRetriever:
            requires_scraping = True

            def __init__(self, query, query_domains=None):
                pass

            def search(self, max_results=5):
                return [{"href": "https://example.org/other", "body": "Other preview"}]

        conductor.researcher.retrievers.append(OtherRetriever)
        await self.run_research(conductor)
        fetched = [url for call in conductor.researcher.scraper_manager.browse_urls.call_args_list
                   for url in call.args[0]]
        self.assertCountEqual(fetched, ["https://example.org/award", "https://example.org/other"])

    async def test_mcp_planning_results_are_not_scraped(self):
        conductor, _ = self.make_conductor()
        conductor.researcher.retrievers[0].__name__ = "MCPRetriever"
        context = await conductor._get_context_from_initial_results(
            "question", [], [{"href": "https://example.org/mcp"}])
        self.assertEqual(context, "")
        conductor.researcher.scraper_manager.browse_urls.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
