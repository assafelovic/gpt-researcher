import os
from unittest.mock import patch

import pytest

from gpt_researcher.memory.embeddings import Memory, _SUPPORTED_PROVIDERS, _get_openai_embedding_model


class TestSupportedProviders:
    def test_openai_is_supported(self):
        assert "openai" in _SUPPORTED_PROVIDERS

    def test_custom_is_supported(self):
        assert "custom" in _SUPPORTED_PROVIDERS

    def test_ollama_is_supported(self):
        assert "ollama" in _SUPPORTED_PROVIDERS

    def test_azure_openai_is_supported(self):
        assert "azure_openai" in _SUPPORTED_PROVIDERS

    def test_supported_providers_are_not_empty(self):
        assert len(_SUPPORTED_PROVIDERS) > 10


class TestGetOpenaiEmbeddingModel:
    def test_default_value_no_env(self):
        model = _get_openai_embedding_model()
        assert model == "text-embedding-3-small"

    def test_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        model = _get_openai_embedding_model()
        assert model == "text-embedding-3-large"


class TestMemoryOpenAIProvider:
    @patch("langchain_openai.OpenAIEmbeddings")
    @patch("gpt_researcher.memory.embeddings.should_use_local_embedding_fallback", return_value=False)
    @patch("gpt_researcher.memory.embeddings.resolve_openai_base_url", return_value=None)
    def test_openai_provider_creates_embeddings(
        self, mock_resolve, mock_should_fallback, mock_embeddings_cls
    ):
        memory = Memory(embedding_provider="openai", model="text-embedding-3-small")
        embeddings = memory.get_embeddings()
        mock_embeddings_cls.assert_called_once()
        assert embeddings is mock_embeddings_cls.return_value

    @patch("langchain_openai.OpenAIEmbeddings")
    @patch("gpt_researcher.memory.embeddings.should_use_local_embedding_fallback", return_value=False)
    @patch("gpt_researcher.memory.embeddings.resolve_openai_base_url", return_value="http://localhost:1234/v1")
    def test_openai_provider_with_local_base_url(
        self, mock_resolve, mock_should_fallback, mock_embeddings_cls
    ):
        memory = Memory(embedding_provider="openai", model="text-embedding-3-small")
        memory.get_embeddings()
        mock_embeddings_cls.assert_called_once()

    @patch("gpt_researcher.memory.embeddings.LocalHashEmbeddings")
    @patch("gpt_researcher.memory.embeddings.should_use_local_embedding_fallback", return_value=True)
    @patch("gpt_researcher.memory.embeddings.resolve_openai_base_url", return_value="http://127.0.0.1:8080/v1")
    def test_openai_provider_with_local_fallback(
        self, mock_resolve, mock_should_fallback, mock_hash_cls
    ):
        memory = Memory(embedding_provider="openai", model="text-embedding-3-small")
        result = memory.get_embeddings()
        mock_hash_cls.assert_called_once()
        assert result is mock_hash_cls.return_value


class TestMemoryCustomProvider:
    @patch("langchain_openai.OpenAIEmbeddings")
    @patch("gpt_researcher.memory.embeddings.should_use_local_embedding_fallback", return_value=False)
    @patch("gpt_researcher.memory.embeddings.resolve_openai_base_url", return_value=None)
    def test_custom_provider_falls_back_to_localhost(
        self, mock_resolve, mock_should_fallback, mock_embeddings_cls
    ):
        with patch.dict(os.environ, {}, clear=True):
            memory = Memory(embedding_provider="custom", model="local-model")
            memory.get_embeddings()
            mock_embeddings_cls.assert_called_once()
            call_kwargs = mock_embeddings_cls.call_args[1]
            assert call_kwargs["base_url"] == "http://localhost:1234/v1"

    @patch("gpt_researcher.memory.embeddings.LocalHashEmbeddings")
    @patch("gpt_researcher.memory.embeddings.should_use_local_embedding_fallback", return_value=True)
    @patch("gpt_researcher.memory.embeddings.resolve_openai_base_url", return_value="http://127.0.0.1:8081/v1")
    def test_custom_provider_local_fallback(
        self, mock_resolve, mock_should_fallback, mock_hash_cls
    ):
        memory = Memory(embedding_provider="custom", model="local-model")
        embeddings = memory.get_embeddings()
        mock_hash_cls.assert_called_once()
        assert embeddings is mock_hash_cls.return_value

    @patch("langchain_openai.OpenAIEmbeddings")
    @patch("gpt_researcher.memory.embeddings.should_use_local_embedding_fallback", return_value=False)
    @patch("gpt_researcher.memory.embeddings.resolve_openai_base_url", return_value="http://my-custom-api:8000/v1")
    def test_custom_provider_with_explicit_base_url(
        self, mock_resolve, mock_should_fallback, mock_embeddings_cls
    ):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            memory = Memory(embedding_provider="custom", model="local-model")
            memory.get_embeddings()
            mock_embeddings_cls.assert_called_once()
            call_kwargs = mock_embeddings_cls.call_args[1]
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["base_url"] == "http://my-custom-api:8000/v1"


class TestMemoryOllamaProvider:
    @patch("langchain_ollama.OllamaEmbeddings")
    @patch("gpt_researcher.memory.embeddings.resolve_ollama_base_url", return_value="http://localhost:11434")
    def test_ollama_provider_creates_embeddings(self, mock_resolve_ollama, mock_embeddings_cls):
        memory = Memory(embedding_provider="ollama", model="nomic-embed-text")
        memory.get_embeddings()
        mock_embeddings_cls.assert_called_once()
        call_kwargs = mock_embeddings_cls.call_args[1]
        assert call_kwargs["base_url"] == "http://localhost:11434"


class TestMemoryAzureOpenAIProvider:
    @patch("langchain_openai.AzureOpenAIEmbeddings")
    def test_azure_openai_provider(self, mock_embeddings_cls, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        memory = Memory(embedding_provider="azure_openai", model="text-embedding-3-small")
        memory.get_embeddings()
        mock_embeddings_cls.assert_called_once()
        call_kwargs = mock_embeddings_cls.call_args[1]
        assert call_kwargs["azure_endpoint"] == "https://test.openai.azure.com"


class TestMemoryUnsupportedProvider:
    def test_unsupported_provider_raises_exception(self):
        with pytest.raises(Exception, match="Embedding not found"):
            Memory(embedding_provider="nonexistent_provider", model="test")


class TestMemoryGetEmbeddings:
    @patch("langchain_openai.OpenAIEmbeddings")
    @patch("gpt_researcher.memory.embeddings.should_use_local_embedding_fallback", return_value=False)
    @patch("gpt_researcher.memory.embeddings.resolve_openai_base_url", return_value=None)
    def test_get_embeddings_returns_not_none(self, mock_resolve, mock_should_fallback, mock_embeddings_cls):
        memory = Memory(embedding_provider="openai", model="text-embedding-3-small")
        embeddings = memory.get_embeddings()
        assert embeddings is not None
