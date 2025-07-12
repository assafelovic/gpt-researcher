"""Tests for post-retrieval processing functionality."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    from gpt_researcher.prompts import post_retrieval_processing
except ImportError:
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))  # Adjust the path to import GPTResearcher from the parent directory
    from gpt_researcher.prompts import post_retrieval_processing

from gpt_researcher.skills.context_manager import ContextManager


@pytest.fixture
def mock_researcher() -> MagicMock:
    """Create a mock researcher for testing."""
    researcher = MagicMock()
    researcher.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS = "Test instructions"
    researcher.cfg.VERBOSE = False
    researcher.agent_role = "Test role"
    researcher.add_costs = MagicMock()
    return researcher


@pytest.fixture
def context_manager(mock_researcher: MagicMock) -> ContextManager:
    """Create a context manager with a mock researcher."""
    return ContextManager(mock_researcher)


@patch("gpt_researcher.skills.context_manager.ContextCompressor")
@patch("gpt_researcher.llm_provider.generic.base.GenericLLMProvider")
async def test_get_similar_content_by_query_with_processing(
    mock_llm_provider_class: MagicMock,
    mock_compressor_class: MagicMock,
    context_manager: ContextManager,
    mock_researcher: MagicMock,
):
    """Test that post-retrieval processing is applied when instructions are provided."""
    # Setup mocks
    mock_compressor = MagicMock()
    mock_compressor.async_get_context = AsyncMock(return_value="Original content")
    mock_compressor_class.return_value = mock_compressor

    mock_llm_provider = MagicMock()
    mock_llm_provider.get_chat_response = AsyncMock(return_value="Processed content")
    mock_llm_provider_class.return_value = mock_llm_provider

    # Call the method
    result = await context_manager.get_similar_content_by_query("test query", [])

    # Verify the results
    assert result == "Processed content"
    mock_compressor.async_get_context.assert_called_once()
    mock_llm_provider.get_chat_response.assert_called_once()

    # Verify the prompt was constructed correctly
    call_args = mock_llm_provider.get_chat_response.call_args[1]
    messages = call_args["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "Test role"
    assert messages[1]["role"] == "user"
    assert "Original content" in messages[1]["content"]
    assert "Test instructions" in messages[1]["content"]


@patch("gpt_researcher.skills.context_manager.ContextCompressor")
@patch("gpt_researcher.llm_provider.generic.base.GenericLLMProvider")
async def test_get_similar_content_by_query_without_processing(
    mock_llm_provider_class: MagicMock,
    mock_compressor_class: MagicMock,
    context_manager: ContextManager,
    mock_researcher: MagicMock,
):
    """Test that post-retrieval processing is not applied when no instructions are provided."""
    # Setup mocks
    mock_compressor = MagicMock()
    mock_compressor.async_get_context = AsyncMock(return_value="Original content")
    mock_compressor_class.return_value = mock_compressor

    # Set instructions to empty
    mock_researcher.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS = ""

    # Call the method
    result = await context_manager.get_similar_content_by_query("test query", [])

    # Verify the results
    assert result == "Original content"
    mock_compressor.async_get_context.assert_called_once()
    mock_llm_provider_class.assert_not_called()


def test_post_retrieval_processing_prompt():
    """Test that the post-retrieval processing prompt is constructed correctly."""
    query = "test query"
    content = "test content"
    instructions = "test instructions"

    prompt = post_retrieval_processing(query, content, instructions)

    assert query in prompt
    assert content in prompt
    assert instructions in prompt

if __name__ == "__main__":
    pytest.main()
