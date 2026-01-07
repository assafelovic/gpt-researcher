import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gpt_researcher.actions.report_generation import (
    write_report_introduction,
    write_conclusion,
    write_research_gap,
    summarize_url,
    generate_draft_section_titles,
    generate_report
)

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.smart_llm_model = "gpt-4"
    config.smart_llm_provider = "openai"
    config.smart_token_limit = 4000
    config.llm_kwargs = {}
    config.language = "english"
    config.report_format = "markdown"
    config.total_words = 1000
    return config

@pytest.fixture
def mock_prompt_family():
    pf = MagicMock()
    pf.generate_report_introduction.return_value = "Intro Prompt"
    pf.generate_report_conclusion.return_value = "Conclusion Prompt"
    pf.generate_research_gap_prompt.return_value = "Gap Prompt"
    pf.generate_draft_titles_prompt.return_value = "Titles Prompt"
    return pf

@patch('gpt_researcher.actions.report_generation.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_write_report_introduction(mock_create_chat, mock_config, mock_prompt_family):
    """Test write_report_introduction success."""
    mock_create_chat.return_value = "Generated Introduction"
    
    result = await write_report_introduction(
        query="test query",
        context="test context",
        agent_role_prompt="You are an agent",
        config=mock_config,
        prompt_family=mock_prompt_family
    )
    
    assert result == "Generated Introduction"
    mock_prompt_family.generate_report_introduction.assert_called_once()
    mock_create_chat.assert_called_once()
    assert mock_create_chat.call_args[1]["messages"][1]["content"] == "Intro Prompt"

@patch('gpt_researcher.actions.report_generation.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_write_conclusion(mock_create_chat, mock_config, mock_prompt_family):
    """Test write_conclusion success."""
    mock_create_chat.return_value = "Generated Conclusion"
    
    result = await write_conclusion(
        query="test query",
        context="test context",
        agent_role_prompt="You are an agent",
        config=mock_config,
        prompt_family=mock_prompt_family
    )
    
    assert result == "Generated Conclusion"
    mock_prompt_family.generate_report_conclusion.assert_called_once()

@patch('gpt_researcher.actions.report_generation.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_write_research_gap(mock_create_chat, mock_config, mock_prompt_family):
    """Test write_research_gap success."""
    mock_create_chat.return_value = "Generated Gap"
    
    result = await write_research_gap(
        query="test query",
        context="test context",
        config=mock_config,
        prompt_family=mock_prompt_family
    )
    
    assert result == "Generated Gap"
    mock_prompt_family.generate_research_gap_prompt.assert_called_once()

@patch('gpt_researcher.actions.report_generation.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_summarize_url(mock_create_chat, mock_config):
    """Test summarize_url success."""
    mock_create_chat.return_value = "Url Summary"
    
    result = await summarize_url(
        url="http://example.com",
        content="Long content",
        role="Agent Role",
        config=mock_config
    )
    
    assert result == "Url Summary"
    assert "Summarize the following content" in mock_create_chat.call_args[1]["messages"][1]["content"]

@patch('gpt_researcher.actions.report_generation.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_generate_draft_section_titles(mock_create_chat, mock_config, mock_prompt_family):
    """Test generate_draft_section_titles parsing."""
    mock_create_chat.return_value = "Title 1\nTitle 2\nTitle 3"
    
    result = await generate_draft_section_titles(
        query="test",
        current_subtopic="sub",
        context="ctx",
        role="role",
        config=mock_config,
        prompt_family=mock_prompt_family
    )
    
    assert result == ["Title 1", "Title 2", "Title 3"]

@patch('gpt_researcher.actions.report_generation.create_chat_completion', new_callable=AsyncMock)
@patch('gpt_researcher.actions.report_generation.get_prompt_by_report_type')
@pytest.mark.asyncio
async def test_generate_report(mock_get_prompt, mock_create_chat, mock_config):
    """Test generate_report flow."""
    mock_create_chat.return_value = "Final Report"
    mock_get_prompt.return_value = lambda *args, **kwargs: "Report Prompt"
    
    result = await generate_report(
        query="test",
        context="ctx",
        agent_role_prompt="role",
        report_type="custom_report",
        report_source="web",
        tone="Formal",
        websocket=None,
        cfg=mock_config
    )
    
    assert result == "Final Report"
    mock_create_chat.assert_called()

@patch('gpt_researcher.actions.report_generation.create_chat_completion', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_write_report_introduction_exception(mock_create_chat, mock_config, mock_prompt_family):
    """Test write_report_introduction exception handling."""
    mock_create_chat.side_effect = Exception("LLM Error")
    
    result = await write_report_introduction(
        query="test",
        context="ctx",
        agent_role_prompt="role",
        config=mock_config
    )
    
    assert result == ""
