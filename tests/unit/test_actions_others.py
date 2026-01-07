import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gpt_researcher.actions.agent_creator import choose_agent
from gpt_researcher.actions.query_processing import (
    get_search_results,
    generate_sub_queries,
    plan_research_outline
)
from gpt_researcher.actions.web_scraping import scrape_urls, filter_urls

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.smart_llm_model = "gpt-4"
    config.smart_llm_provider = "openai"
    config.llm_kwargs = {}
    config.strategic_llm_model = "gpt-4"
    config.strategic_llm_provider = "openai"
    config.excluded_domains = ["exclude.com"]
    return config

# --- Agent Creator Tests ---

@patch('gpt_researcher.actions.agent_creator.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_choose_agent_success(mock_create_chat, mock_config):
    """Test choose_agent with valid JSON response."""
    mock_create_chat.return_value = json.dumps({
        "server": "Test Agent",
        "agent_role_prompt": "Test Prompt"
    })
    
    agent, prompt = await choose_agent("query", mock_config)
    assert agent == "Test Agent"
    assert prompt == "Test Prompt"

@patch('gpt_researcher.actions.agent_creator.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_choose_agent_failure(mock_create_chat, mock_config):
    """Test choose_agent with invalid response (fallback)."""
    mock_create_chat.return_value = "Not JSON"
    
    agent, prompt = await choose_agent("query", mock_config)
    assert agent == "Default Agent"
    assert "critical thinker" in prompt

# --- Query Processing Tests ---

@pytest.mark.asyncio
async def test_get_search_results():
    """Test get_search_results interactions with retriever."""
    mock_retriever_cls = MagicMock()
    mock_retriever_cls.__name__ = "MockRetriever"
    mock_instance = MagicMock()
    mock_retriever_cls.return_value = mock_instance
    mock_instance.search.return_value = [{"url": "http://test.com"}]
    
    results = await get_search_results("query", mock_retriever_cls)
    
    assert results == [{"url": "http://test.com"}]
    mock_retriever_cls.assert_called_with("query", query_domains=None)

@patch('gpt_researcher.actions.query_processing.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_generate_sub_queries(mock_create_chat, mock_config):
    """Test generate_sub_queries parsing."""
    mock_create_chat.return_value = '["q1", "q2"]'
    
    queries = await generate_sub_queries(
        query="test",
        parent_query="parent",
        report_type="report",
        context=[],
        cfg=mock_config
    )
    
    assert queries == ["q1", "q2"]

@pytest.mark.asyncio
async def test_plan_research_outline_mcp_only(mock_config):
    """Test plan_research_outline skipping generation for MCP only."""
    queries = await plan_research_outline(
        query="test",
        search_results=[],
        agent_role_prompt="role",
        cfg=mock_config,
        parent_query="parent",
        report_type="report",
        retriever_names=["MCPRetriever"]
    )
    
    assert queries == ["test"]  # Should return original query only

# --- Web Scraping Tests ---

@pytest.mark.asyncio
async def test_filter_urls(mock_config):
    """Test URL filtering."""
    urls = ["http://good.com", "http://exclude.com/page"]
    filtered = await filter_urls(urls, mock_config)
    assert filtered == ["http://good.com"]

@patch('gpt_researcher.actions.web_scraping.Scraper')
@pytest.mark.asyncio
async def test_scrape_urls(mock_scraper_cls, mock_config):
    """Test scrape_urls orchestration."""
    mock_pool = MagicMock()
    mock_scraper_instance = AsyncMock()
    mock_scraper_cls.return_value = mock_scraper_instance
    
    mock_scraper_instance.run.return_value = [
        {"url": "http://test.com", "content": "data", "image_urls": ["img1.jpg"]}
    ]
    
    data, images = await scrape_urls(["http://test.com"], mock_config, mock_pool)
    
    assert len(data) == 1
    assert data[0]["url"] == "http://test.com"
    assert images == ["img1.jpg"]
