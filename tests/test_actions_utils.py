from unittest.mock import AsyncMock, MagicMock

import pytest

from gpt_researcher.actions.utils import (
    calculate_cost,
    format_token_count,
    stream_output,
    safe_send_json,
    update_cost,
)


class TestCalculateCost:
    def test_known_model(self):
        cost = calculate_cost(100, 50, "gpt-4o-mini")
        assert cost == (150 / 1000) * 0.000001

    def test_unknown_model(self):
        cost = calculate_cost(100, 50, "unknown-model")
        assert cost == 0.0001

    def test_case_insensitive(self):
        cost1 = calculate_cost(100, 50, "GPT-4o-mini")
        cost2 = calculate_cost(100, 50, "gpt-4o-mini")
        assert cost1 == cost2

    def test_zero_tokens(self):
        cost = calculate_cost(0, 0, "gpt-4o")
        assert cost == 0.0


class TestFormatTokenCount:
    def test_small_number(self):
        assert format_token_count(0) == "0"
        assert format_token_count(100) == "100"

    def test_large_number(self):
        assert format_token_count(1000) == "1,000"
        assert format_token_count(1500000) == "1,500,000"


class TestStreamOutput:
    @pytest.mark.asyncio
    async def test_with_websocket(self):
        ws = AsyncMock()
        await stream_output("logs", "content", "output", websocket=ws)
        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_without_websocket(self):
        await stream_output("logs", "content", "output", websocket=None)
        assert True

    @pytest.mark.asyncio
    async def test_images_type_skips_log(self):
        ws = AsyncMock()
        await stream_output("images", "content", "output", websocket=ws)
        ws.send_json.assert_called_once()


class TestSafeSendJson:
    @pytest.mark.asyncio
    async def test_successful_send(self):
        ws = AsyncMock()
        await safe_send_json(ws, {"key": "value"})
        ws.send_json.assert_called_once_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_closed_websocket(self):
        ws = AsyncMock()
        ws.send_json.side_effect = Exception("WebSocket closed")
        await safe_send_json(ws, {"key": "value"})
        assert True

    @pytest.mark.asyncio
    async def test_timeout(self):
        ws = AsyncMock()
        ws.send_json.side_effect = Exception("timeout error")
        await safe_send_json(ws, {"key": "value"})
        assert True


class TestUpdateCost:
    @pytest.mark.asyncio
    async def test_update_cost_sends_message(self):
        ws = AsyncMock()
        await update_cost(100, 50, "gpt-4o-mini", ws)
        ws.send_json.assert_called_once()


class TestGetConfigDict:
    def test_basic_config_dict(self):
        from backend.server.server_utils import get_config_dict
        result = get_config_dict()
        assert isinstance(result, dict)
        assert "OPENAI_API_KEY" in result
        assert "TAVILY_API_KEY" in result
        assert "RETRIEVER" in result

    def test_config_dict_with_overrides(self):
        from backend.server.server_utils import get_config_dict
        result = get_config_dict(openai_api_key="test-key-123")
        assert result["OPENAI_API_KEY"] == "test-key-123"
        assert result["TAVILY_API_KEY"] == ""

    def test_config_dict_static_keys(self):
        from backend.server.server_utils import get_config_dict
        result = get_config_dict()
        assert result["LANGCHAIN_TRACING_V2"] in ("true", "")
        assert result["DOC_PATH"] == "./my-docs"