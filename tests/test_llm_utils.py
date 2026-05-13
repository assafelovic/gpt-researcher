from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt_researcher.utils.llm import create_chat_completion, get_llm


class TestCreateChatCompletionValidation:
    @pytest.mark.asyncio
    async def test_model_none_raises_value_error(self):
        with pytest.raises(ValueError, match="darf nicht `None` sein"):
            await create_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                model=None,
            )

    @pytest.mark.asyncio
    async def test_max_tokens_exceeds_limit(self):
        with pytest.raises(ValueError, match="Max tokens cannot be more than 32,000"):
            await create_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                model="gpt-4o-mini",
                max_tokens=99999,
            )


class TestCreateChatCompletion:
    @pytest.mark.asyncio
    async def test_streaming_with_websocket(self):
        mock_provider = AsyncMock()
        mock_provider.get_chat_response.return_value = "streamed response"

        with patch("gpt_researcher.utils.llm.get_llm", return_value=mock_provider):
            result = await create_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                model="gpt-4o-mini",
                llm_provider="openai",
                stream=True,
            )
            assert result == "streamed response"

    @pytest.mark.asyncio
    async def test_non_streaming(self):
        mock_provider = AsyncMock()
        mock_provider.get_chat_response.return_value = "non-streamed response"

        with patch("gpt_researcher.utils.llm.get_llm", return_value=mock_provider):
            result = await create_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                model="gpt-4o-mini",
                llm_provider="openai",
                stream=False,
            )
            assert result == "non-streamed response"

    @pytest.mark.asyncio
    async def test_with_cost_callback(self):
        mock_provider = AsyncMock()
        mock_provider.get_chat_response.return_value = "response with cost"

        cost_callback = MagicMock()

        with patch("gpt_researcher.utils.llm.get_llm", return_value=mock_provider):
            result = await create_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                model="gpt-4o-mini",
                llm_provider="openai",
                cost_callback=cost_callback,
            )
            assert result == "response with cost"

    @pytest.mark.asyncio
    async def test_with_reasoning_effort_model(self):
        mock_provider = AsyncMock()
        mock_provider.get_chat_response.return_value = "reasoned response"

        with patch("gpt_researcher.utils.llm.get_llm", return_value=mock_provider):
            result = await create_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                model="o3-mini",
                llm_provider="openai",
                reasoning_effort="high",
            )
            assert result == "reasoned response"

    @pytest.mark.asyncio
    async def test_provider_fallback_to_model_prefix(self):
        mock_provider = AsyncMock()
        mock_provider.get_chat_response.return_value = "fallback response"

        with patch("gpt_researcher.utils.llm.get_llm", return_value=mock_provider):
            result = await create_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                model="openai:gpt-4o-mini",
            )
            assert result == "fallback response"