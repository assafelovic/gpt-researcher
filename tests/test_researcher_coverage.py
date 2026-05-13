from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gpt_researcher.skills.researcher import (
    ResearchConductor,
    _dedupe_queries,
)


class TestDedupeQueries:
    def test_empty_input(self):
        assert _dedupe_queries([]) == []

    def test_no_duplicates(self):
        result = _dedupe_queries(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_duplicates_removed(self):
        result = _dedupe_queries(["hello world", "hello world", "foo"])
        assert result == ["hello world", "foo"]

    def test_case_insensitive_dedup(self):
        result = _dedupe_queries(["Hello", "hello", "HELLO"])
        assert result == ["Hello"]

    def test_empty_strings_skipped(self):
        result = _dedupe_queries(["a", "", "b", "  ", "c"])
        assert result == ["a", "b", "c"]

    def test_whitespace_normalized(self):
        result = _dedupe_queries(["hello   world", "hello world"])
        assert len(result) == 1

    def test_none_values_skipped(self):
        result = _dedupe_queries(["a", "b"])
        assert result == ["a", "b"]


class FakeResearcher:
    def __init__(self, **overrides):
        self.retrievers = []
        self.cfg = SimpleNamespace(
            curate_sources=False,
            max_search_results_per_query=5,
            mcp_strategy="fast",
            doc_path="./my-docs",
        )
        self.visited_urls = set()
        self.verbose = False
        self.websocket = None
        self.query_domains = []
        self.report_source = "web"
        self.query = "test query"
        self.agent = "test-agent"
        self.role = "test-role"
        self.headers = {}
        self.kwargs = {}
        self.mcp_strategy = None
        self.context = []
        self.source_urls = []
        self.document_urls = []
        self.complement_source_urls = False
        self.documents = None
        self.vector_store = None
        self.vector_store_filter = None
        self.report_type = "research_report"
        self.parent_query = ""
        self.source_curator = MagicMock()
        self.source_curator.curate_sources = AsyncMock(side_effect=lambda x: x)
        self.context_manager = MagicMock()
        self.context_manager.get_similar_content_by_query = AsyncMock(return_value="mocked context")
        self.scraper_manager = MagicMock()
        self.scraper_manager.browse_urls = AsyncMock(return_value=[])
        self.prompt_family = MagicMock()
        self.prompt_family.join_local_web_documents = MagicMock(side_effect=lambda a, b: a + b)

        def add_costs(cost):
            pass
        self.add_costs = add_costs

        def get_costs():
            return 0.0
        self.get_costs = get_costs
        for k, v in overrides.items():
            setattr(self, k, v)


class TestResearchConductorInit:
    def test_onion_mode(self):
        researcher = FakeResearcher(report_source="onion")
        conductor = ResearchConductor(researcher)
        assert conductor._is_onion_mode() is True

    def test_not_onion_mode(self):
        conductor = ResearchConductor(FakeResearcher())
        assert conductor._is_onion_mode() is False

    def test_primary_retriever_onion(self):
        researcher = FakeResearcher(
            report_source="onion",
            retrievers=[],
        )
        conductor = ResearchConductor(researcher)
        from gpt_researcher.retrievers import Duckduckgo
        assert conductor._primary_retriever_class() is Duckduckgo

    def test_primary_retriever_web(self):
        researcher = FakeResearcher()
        researcher.retrievers = ["custom_retriever"]
        conductor = ResearchConductor(researcher)
        assert conductor._primary_retriever_class() == "custom_retriever"


class TestGetMCPStrategy:
    def test_instance_level(self):
        researcher = FakeResearcher(mcp_strategy="deep")
        conductor = ResearchConductor(researcher)
        assert conductor._get_mcp_strategy() == "deep"

    def test_config_level(self):
        researcher = FakeResearcher(mcp_strategy=None)
        researcher.cfg.mcp_strategy = "disabled"
        conductor = ResearchConductor(researcher)
        assert conductor._get_mcp_strategy() == "disabled"

    def test_default_fast(self):
        researcher = FakeResearcher(mcp_strategy=None)
        if hasattr(researcher.cfg, "mcp_strategy"):
            del researcher.cfg.mcp_strategy
        conductor = ResearchConductor(researcher)
        assert conductor._get_mcp_strategy() == "fast"


class TestCombineMCPAndWebContext:
    def test_both_empty(self):
        conductor = ResearchConductor(FakeResearcher())
        result = conductor._combine_mcp_and_web_context([], "", "test query")
        assert result == ""

    def test_only_web_context(self):
        conductor = ResearchConductor(FakeResearcher())
        result = conductor._combine_mcp_and_web_context([], "web content", "test query")
        assert "web content" in result

    def test_only_mcp_context(self):
        conductor = ResearchConductor(FakeResearcher())
        mcp_ctx = [{"content": "mcp result", "url": "https://example.com", "title": "MCP Doc"}]
        result = conductor._combine_mcp_and_web_context(mcp_ctx, "", "test query")
        assert "mcp result" in result
        assert "example.com" in result

    def test_mcp_without_url(self):
        conductor = ResearchConductor(FakeResearcher())
        mcp_ctx = [{"content": "llm analysis", "url": "mcp://llm_analysis", "title": "LLM"}]
        result = conductor._combine_mcp_and_web_context(mcp_ctx, "", "test query")
        assert "llm analysis" in result
        assert "mcp://llm_analysis" not in result

    def test_both_combined(self):
        conductor = ResearchConductor(FakeResearcher())
        mcp_ctx = [{"content": "mcp result", "url": "https://example.com", "title": "MCP"}]
        result = conductor._combine_mcp_and_web_context(mcp_ctx, "web content", "test query")
        assert "web content" in result
        assert "mcp result" in result


class TestResolveProxyURL:
    def test_onion_with_proxy(self):
        researcher = FakeResearcher(report_source="onion")
        researcher.cfg.onion_proxy_url = "socks5://localhost:9050"
        conductor = ResearchConductor(researcher)
        url = conductor._resolve_proxy_url()
        assert url == "socks5://localhost:9050"

    def test_not_onion_returns_none(self):
        conductor = ResearchConductor(FakeResearcher())
        assert conductor._resolve_proxy_url() is None

    def test_onion_without_proxy(self):
        researcher = FakeResearcher(report_source="onion")
        researcher.cfg.onion_proxy_url = None
        conductor = ResearchConductor(researcher)
        assert conductor._resolve_proxy_url() is None


class TestGetNewUrls:
    @pytest.mark.asyncio
    async def test_new_urls_added(self):
        conductor = ResearchConductor(FakeResearcher())
        urls = await conductor._get_new_urls(["https://example.com/a", "https://example.com/b"])
        assert urls == ["https://example.com/a", "https://example.com/b"]
        assert "https://example.com/a" in conductor.researcher.visited_urls

    @pytest.mark.asyncio
    async def test_duplicate_urls_skipped(self):
        conductor = ResearchConductor(FakeResearcher())
        conductor.researcher.visited_urls.add("https://example.com/a")
        urls = await conductor._get_new_urls(["https://example.com/a", "https://example.com/b"])
        assert urls == ["https://example.com/b"]


class TestConductResearch:
    @pytest.mark.asyncio
    async def test_web_source_research(self):
        researcher = FakeResearcher()
        conductor = ResearchConductor(researcher)
        conductor._get_context_by_web_search = AsyncMock(return_value=["web context"])
        result = await conductor.conduct_research()
        conductor._get_context_by_web_search.assert_called_once()
        assert result == ["web context"]

    @pytest.mark.asyncio
    async def test_source_urls_research(self):
        researcher = FakeResearcher(source_urls=["https://example.com"])
        conductor = ResearchConductor(researcher)
        conductor._get_context_by_urls = AsyncMock(return_value=["url context"])
        result = await conductor.conduct_research()
        conductor._get_context_by_urls.assert_called_once()
        assert result == ["url context"]

    @pytest.mark.asyncio
    async def test_get_context_by_web_search_error_returns_empty(self):
        conductor = ResearchConductor(FakeResearcher())
        conductor.plan_research = AsyncMock(return_value=["subq1"])
        conductor._process_sub_query = AsyncMock(side_effect=Exception("gather failed"))
        result = await conductor._get_context_by_web_search("test query", [], [])
        assert result == []


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        class FakeRetriever:
            __name__ = "FakeRetriever"

            def __init__(self, query, **kwargs):
                pass

            def search(self, max_results=5):
                return [{"title": "Result 1", "href": "https://example.com/1"}]

        conductor = ResearchConductor(FakeResearcher())
        results = await conductor._search(FakeRetriever, "test query")
        assert len(results) == 1
        assert results[0]["title"] == "Result 1"

    @pytest.mark.asyncio
    async def test_search_no_method_returns_empty(self):
        class FakeRetriever:
            __name__ = "FakeRetriever"

            def __init__(self, query, **kwargs):
                pass

        conductor = ResearchConductor(FakeResearcher())
        results = await conductor._search(FakeRetriever, "test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_exception_returns_empty(self):
        class FakeRetriever:
            __name__ = "FakeRetriever"

            def __init__(self, query, **kwargs):
                raise RuntimeError("init failed")

        conductor = ResearchConductor(FakeResearcher())
        results = await conductor._search(FakeRetriever, "test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_mcp_retriever_logging(self):
        class MCPRetriever:
            __name__ = "MCPRetriever"

            def __init__(self, query, **kwargs):
                pass

            def search(self, max_results=5):
                return [{"title": "MCP Result", "href": "https://mcp.example.com/1", "body": "content"}]

        researcher = FakeResearcher(verbose=True)
        conductor = ResearchConductor(researcher)
        results = await conductor._search(MCPRetriever, "test query")
        assert len(results) == 1


class TestExtractContent:
    @pytest.mark.asyncio
    async def test_empty_results_returns_empty(self):
        conductor = ResearchConductor(FakeResearcher())
        result = await conductor._extract_content([])
        assert result == []

    @pytest.mark.asyncio
    async def test_no_href_in_results_returns_empty(self):
        conductor = ResearchConductor(FakeResearcher())
        result = await conductor._extract_content([{"title": "no href"}])
        assert result == []

    @pytest.mark.asyncio
    async def test_all_urls_already_visited(self):
        researcher = FakeResearcher()
        researcher.visited_urls.add("https://example.com/1")
        conductor = ResearchConductor(researcher)
        result = await conductor._extract_content([{"href": "https://example.com/1"}])
        assert result == []


class TestSummarizeContent:
    @pytest.mark.asyncio
    async def test_empty_content_returns_empty(self):
        conductor = ResearchConductor(FakeResearcher())
        result = await conductor._summarize_content("test query", [])
        assert result == ""


class TestUpdateSearchProgress:
    @pytest.mark.asyncio
    async def test_progress_update_with_websocket(self):
        researcher = FakeResearcher(verbose=True)
        conductor = ResearchConductor(researcher)
        await conductor._update_search_progress(2, 10)
        assert True


class TestSearchRelevantSourceUrls:
    @pytest.mark.asyncio
    async def test_no_mcp_retrievers_skipped(self, monkeypatch):
        class FakeRetriever:
            __name__ = "FakeRetriever"

            def __init__(self, query, **kwargs):
                pass

            def search(self, max_results=5):
                return []

        researcher = FakeResearcher()
        conductor = ResearchConductor(researcher)
        urls, prefetched = await conductor._search_relevant_source_urls("test query")
        assert urls == []
        assert prefetched == []

    @pytest.mark.asyncio
    async def test_mcp_retriever_skipped(self):
        class MCPRetriever:
            __name__ = "MCPRetriever"

            def __init__(self, query, **kwargs):
                pass

            def search(self, max_results=5):
                return []

        researcher = FakeResearcher(retrievers=[MCPRetriever])
        conductor = ResearchConductor(researcher)
        urls, prefetched = await conductor._search_relevant_source_urls("test query")
        assert urls == []

    @pytest.mark.asyncio
    async def test_prefetched_content_collected(self, monkeypatch):
        class FakeRetriever:
            __name__ = "FakeRetriever"

            def __init__(self, query, **kwargs):
                pass

            def search(self, max_results=5):
                return [{
                    "href": "https://example.com/full",
                    "raw_content": "full content here " * 10,
                    "title": "Full Article",
                }]

        researcher = FakeResearcher(retrievers=[FakeRetriever])
        conductor = ResearchConductor(researcher)
        urls, prefetched = await conductor._search_relevant_source_urls("test query")
        assert len(prefetched) == 1
        assert prefetched[0]["url"] == "https://example.com/full"