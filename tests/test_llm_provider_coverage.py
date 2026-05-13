import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_chat_openai():
    with patch("langchain_openai.ChatOpenAI") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock, mock_instance


@pytest.fixture
def mock_azure_chat_openai():
    with patch("langchain_openai.AzureChatOpenAI") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock, mock_instance


class TestChatLogger:
    @pytest.mark.asyncio
    async def test_log_request(self, tmp_path):
        from gpt_researcher.llm_provider.generic.base import ChatLogger
        log_file = tmp_path / "chat.log"
        logger = ChatLogger(str(log_file))
        await logger.log_request(
            messages=[{"role": "user", "content": "hello"}],
            response="world"
        )
        content = log_file.read_text()
        assert "hello" in content
        assert "world" in content

    def test_chat_logger_init(self, tmp_path):
        from gpt_researcher.llm_provider.generic.base import ChatLogger
        logger = ChatLogger(str(tmp_path / "test.log"))
        assert logger.fname == str(tmp_path / "test.log")
        assert logger._lock is not None


class TestGenericLLMProvider:
    def test_init_with_chat_log(self, tmp_path):
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
        mock_llm = MagicMock()
        provider = GenericLLMProvider(mock_llm, chat_log=str(tmp_path / "test.log"))
        assert provider.chat_logger is not None

    def test_init_without_chat_log(self):
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
        mock_llm = MagicMock()
        provider = GenericLLMProvider(mock_llm, chat_log=None)
        assert provider.chat_logger is None

    @pytest.mark.asyncio
    async def test_get_chat_response(self):
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "response text"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        provider = GenericLLMProvider(mock_llm)
        result = await provider.get_chat_response(messages=[{"role": "user", "content": "hi"}], stream=False)
        assert result == "response text"

    @pytest.mark.asyncio
    async def test_get_chat_response_with_stream(self):
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

        mock_llm = MagicMock()

        async def fake_stream(messages):
            chunks = [MagicMock(content="Hel"), MagicMock(content="lo")]
            for c in chunks:
                yield c

        mock_llm.astream = fake_stream

        mock_ws = AsyncMock()
        provider = GenericLLMProvider(mock_llm)
        result = await provider.get_chat_response(
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
            websocket=mock_ws,
        )
        assert result == "Hello"


class TestFromProvider:
    @patch("gpt_researcher.llm_provider.generic.base.resolve_openai_base_url", return_value=None)
    def test_openai_provider(self, mock_resolve, mock_chat_openai):
        MockChatOpenAI, mock_instance = mock_chat_openai
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

        provider = GenericLLMProvider.from_provider("openai", model="gpt-4o-mini")
        MockChatOpenAI.assert_called_once()
        assert provider.llm is mock_instance

    @patch("gpt_researcher.llm_provider.generic.base.resolve_openai_base_url", return_value="http://localhost:8080/v1")
    @patch("gpt_researcher.llm_provider.generic.base.is_local_openai_base_url", return_value=True)
    def test_openai_local_base_url(self, mock_is_local, mock_resolve, mock_chat_openai):
        MockChatOpenAI, mock_instance = mock_chat_openai
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

        provider = GenericLLMProvider.from_provider("openai", model="gpt-4o-mini")
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["openai_api_base"] == "http://localhost:8080/v1"

    @patch("gpt_researcher.llm_provider.generic.base.resolve_openai_base_url", return_value=None)
    def test_openai_request_timeout_conversion(self, mock_resolve, mock_chat_openai):
        MockChatOpenAI, mock_instance = mock_chat_openai
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

        provider = GenericLLMProvider.from_provider(
            "openai", model="gpt-4o-mini", request_timeout=30.0
        )
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["timeout"] == 30.0
        assert "request_timeout" not in call_kwargs

    @patch("gpt_researcher.llm_provider.generic.base.resolve_openai_base_url", return_value=None)
    def test_openai_max_tokens_conversion(self, mock_resolve, mock_chat_openai):
        MockChatOpenAI, mock_instance = mock_chat_openai
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

        provider = GenericLLMProvider.from_provider(
            "openai", model="gpt-4o-mini", max_tokens=4000
        )
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["max_completion_tokens"] == 4000
        assert "max_tokens" not in call_kwargs

    @patch("gpt_researcher.llm_provider.generic.base.resolve_openai_base_url", return_value=None)
    def test_openai_local_api_key_added(self, mock_resolve, mock_chat_openai, monkeypatch):
        MockChatOpenAI, mock_instance = mock_chat_openai
        monkeypatch.setenv("OPENAI_API_KEY", "test-local-key")
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

        provider = GenericLLMProvider.from_provider(
            "openai", model="gpt-4o-mini", openai_api_base="http://localhost:8080"
        )
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["openai_api_key"] == "test-local-key"

    @patch("gpt_researcher.llm_provider.generic.base.resolve_openai_base_url", return_value=None)
    def test_openai_local_without_key_falls_back(self, mock_resolve, mock_chat_openai, monkeypatch):
        MockChatOpenAI, mock_instance = mock_chat_openai
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

        provider = GenericLLMProvider.from_provider(
            "openai", model="gpt-4o-mini", openai_api_base="http://localhost:8080"
        )
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["openai_api_key"] == "sk-local"


class TestReasoningEfforts:
    def test_enum_values(self):
        from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
        assert ReasoningEfforts.High.value == "high"
        assert ReasoningEfforts.Medium.value == "medium"
        assert ReasoningEfforts.Low.value == "low"


class TestConstants:
    def test_no_support_temperature_models(self):
        from gpt_researcher.llm_provider.generic.base import NO_SUPPORT_TEMPERATURE_MODELS
        assert "o3-mini" in NO_SUPPORT_TEMPERATURE_MODELS
        assert "o1" in NO_SUPPORT_TEMPERATURE_MODELS

    def test_supported_providers(self):
        from gpt_researcher.llm_provider.generic.base import _SUPPORTED_PROVIDERS
        assert "openai" in _SUPPORTED_PROVIDERS
        assert "anthropic" in _SUPPORTED_PROVIDERS
        assert "ollama" in _SUPPORTED_PROVIDERS

    def test_support_reasoning_effort_models(self):
        from gpt_researcher.llm_provider.generic.base import SUPPORT_REASONING_EFFORT_MODELS
        assert "o3-mini" in SUPPORT_REASONING_EFFORT_MODELS