from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_llm_provider():
    with patch("gpt_researcher.llm_provider.generic.base.GenericLLMProvider.from_provider") as mock_from:
        mock_instance = MagicMock()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "mock answer"
        mock_response.tool_calls = None
        mock_ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.ainvoke = mock_ainvoke
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_instance.llm = mock_llm
        mock_from.return_value = mock_instance
        yield mock_from, mock_instance, mock_llm


@pytest.mark.asyncio
async def test_create_chat_completion_with_tools_no_tool_calls(mock_llm_provider):
    mock_from, mock_instance, mock_llm = mock_llm_provider
    mock_response = MagicMock()
    mock_response.content = "direct answer"
    mock_response.tool_calls = None
    mock_llm.ainvoke.return_value = mock_response

    from gpt_researcher.utils.tools import create_chat_completion_with_tools

    response, metadata = await create_chat_completion_with_tools(
        messages=[{"role": "user", "content": "hello"}],
        tools=[],
        model="gpt-4o-mini",
        llm_provider="openai",
    )
    assert response == "direct answer"
    assert metadata == []


@pytest.mark.asyncio
async def test_create_chat_completion_with_temperature_and_max_tokens(mock_llm_provider):
    mock_from, mock_instance, mock_llm = mock_llm_provider

    mock_response = MagicMock()
    mock_response.content = "answer"
    mock_response.tool_calls = None
    mock_llm.ainvoke.return_value = mock_response

    from gpt_researcher.utils.tools import create_chat_completion_with_tools

    response, metadata = await create_chat_completion_with_tools(
        messages=[{"role": "user", "content": "hi"}],
        tools=[],
        model="gpt-4o-mini",
        temperature=0.8,
        max_tokens=2000,
        timeout=30.0,
        llm_provider="openai",
    )
    assert response == "answer"

    call_kwargs = mock_from.call_args
    assert call_kwargs[1]["temperature"] == 0.8
    assert call_kwargs[1]["max_tokens"] == 2000
    assert call_kwargs[1]["timeout"] == 30.0


@pytest.mark.asyncio
async def test_assistant_message_conversion(mock_llm_provider):
    mock_from, mock_instance, mock_llm = mock_llm_provider

    mock_response = MagicMock()
    mock_response.content = "hello back"
    mock_response.tool_calls = None
    mock_llm.ainvoke.return_value = mock_response

    from gpt_researcher.utils.tools import create_chat_completion_with_tools

    response, metadata = await create_chat_completion_with_tools(
        messages=[
            {"role": "assistant", "content": "let me help"},
            {"role": "user", "content": "help me"},
        ],
        tools=[],
        model="gpt-4o-mini",
        llm_provider="openai",
    )
    assert response == "hello back"