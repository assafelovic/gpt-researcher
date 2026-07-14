"""Skip redundant Tavily MCP when direct Tavily retriever is active (#1875)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gpt_researcher.skills.researcher import ResearchConductor


class TavilySearch:
    pass


class MCPRetriever:  # name contains mcpretriever
    pass


@pytest.mark.asyncio
async def test_redundant_tavily_mcp_is_skipped():
    conductor = ResearchConductor(SimpleNamespace(
        retrievers=[TavilySearch, MCPRetriever],
        mcp_configs=[{"name": "tavily-mcp", "command": "npx", "args": ["-y", "tavily-mcp@0.1.2"]}],
        mcp_strategy="fast",
        verbose=False,
        websocket=None,
        headers={},
        query_domains=[],
        cfg=SimpleNamespace(max_search_results_per_query=5),
        kwargs={},
        context_manager=SimpleNamespace(
            get_similar_content_by_query=AsyncMock(return_value="web-context")
        ),
    ))
    conductor._mcp_results_cache = None
    conductor._execute_mcp_research_for_queries = AsyncMock(return_value=["should-not-run"])
    conductor._scrape_data_by_urls = AsyncMock(return_value=[{"url": "u", "raw_content": "c"}])
    conductor._combine_mcp_and_web_context = MagicMock(return_value="combined")

    out = await conductor._process_sub_query("topic")

    conductor._execute_mcp_research_for_queries.assert_not_called()
    assert out == "combined"


@pytest.mark.asyncio
async def test_non_tavily_mcp_still_runs():
    conductor = ResearchConductor(SimpleNamespace(
        retrievers=[TavilySearch, MCPRetriever],
        mcp_configs=[{"name": "filesystem", "command": "npx", "args": ["@modelcontextprotocol/server-filesystem", "/tmp"]}],
        mcp_strategy="deep",
        verbose=False,
        websocket=None,
        headers={},
        query_domains=[],
        cfg=SimpleNamespace(max_search_results_per_query=5),
        kwargs={},
        context_manager=SimpleNamespace(
            get_similar_content_by_query=AsyncMock(return_value="web-context")
        ),
    ))
    conductor._execute_mcp_research_for_queries = AsyncMock(return_value=["mcp-context"])
    conductor._scrape_data_by_urls = AsyncMock(return_value=[{"url": "u", "raw_content": "c"}])
    conductor._combine_mcp_and_web_context = MagicMock(return_value="combined")

    await conductor._process_sub_query("topic")
    conductor._execute_mcp_research_for_queries.assert_called()
