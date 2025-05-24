from __future__ import annotations

import logging
import os

from typing import Any

OPENAI_EMBEDDING_MODEL: str = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

logger: logging.Logger = logging.getLogger(__name__)

_SUPPORTED_PROVIDERS: set[str] = {
    "azure_openai",
    "bedrock",
    "cohere",
    "custom",
    "dashscope",
    "fireworks",
    "gigachat",
    "google_genai",
    "google_vertexai",
    "huggingface",
    "mistralai",
    "nomic",
    "ollama",
    "openai",
    "together",
    "voyageai",
}


class Memory:
    def __init__(
        self,
        embedding_provider: str,
        model: str,
        **embdding_kwargs: Any,
    ):
        _embeddings: Any | None = None
        match embedding_provider:
            case "custom":
                from langchain_openai import OpenAIEmbeddings

                _embeddings = OpenAIEmbeddings(
                    model=model,
                    openai_api_key=os.getenv("OPENAI_API_KEY", "custom"),  # pyright: ignore[reportCallIssue]
                    openai_api_base=os.getenv(  # pyright: ignore[reportCallIssue]
                        "OPENAI_BASE_URL",
                        "http://localhost:1234/v1",
                    ),
                    check_embedding_ctx_length=False,
                    **embdding_kwargs,
                )  # quick fix for lmstudio
            case "openai":
                from langchain_openai import OpenAIEmbeddings

                _embeddings = OpenAIEmbeddings(model=model, **embdding_kwargs)
            case "azure_openai":
                from langchain_openai import AzureOpenAIEmbeddings

                _embeddings = AzureOpenAIEmbeddings(
                    model=model,
                    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],  # pyright: ignore[reportCallIssue]
                    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],  # pyright: ignore[reportCallIssue]
                    **embdding_kwargs,
                )
            case "cohere":
                from langchain_cohere import CohereEmbeddings

                _embeddings = CohereEmbeddings(model=model, **embdding_kwargs)
            case "google_vertexai":
                from langchain_google_vertexai import VertexAIEmbeddings

                _embeddings = VertexAIEmbeddings(model=model, **embdding_kwargs)
            case "google_genai":
                from langchain_google_genai import GoogleGenerativeAIEmbeddings

                _embeddings = GoogleGenerativeAIEmbeddings(model=model, **embdding_kwargs)
            case "fireworks":
                from langchain_fireworks import FireworksEmbeddings

                _embeddings = FireworksEmbeddings(model=model, **embdding_kwargs)
            case "gigachat":
                from langchain_gigachat import GigaChatEmbeddings

                _embeddings = GigaChatEmbeddings(model=model, **embdding_kwargs)
            case "ollama":
                from langchain_ollama import OllamaEmbeddings

                _embeddings = OllamaEmbeddings(model=model, base_url=os.environ["OLLAMA_BASE_URL"], **embdding_kwargs)
            case "together":
                from langchain_together import TogetherEmbeddings

                _embeddings = TogetherEmbeddings(model=model, **embdding_kwargs)
            case "mistralai":
                from langchain_mistralai import MistralAIEmbeddings

                _embeddings = MistralAIEmbeddings(model=model, **embdding_kwargs)
            case "huggingface":
                from langchain_huggingface import HuggingFaceEmbeddings

                _embeddings = HuggingFaceEmbeddings(model_name=model, **embdding_kwargs)
            case "nomic":
                from langchain_nomic import NomicEmbeddings

                _embeddings = NomicEmbeddings(model=model, **embdding_kwargs)
            case "voyageai":
                from langchain_voyageai import VoyageAIEmbeddings

                _embeddings = VoyageAIEmbeddings(voyage_api_key=os.environ["VOYAGE_API_KEY"], model=model, **embdding_kwargs)
            case "dashscope":
                from langchain_community.embeddings import DashScopeEmbeddings

                _embeddings = DashScopeEmbeddings(model=model, **embdding_kwargs)
            case "bedrock":
                from langchain_aws.embeddings import BedrockEmbeddings

                _embeddings = BedrockEmbeddings(model_id=model, **embdding_kwargs)
            case _:
                raise Exception(f"Embedding provider {embedding_provider} not found.")

        self._embeddings = _embeddings

    def get_embeddings(self) -> Any:
        return self._embeddings


class FallbackMemory(Memory):
    """Memory with fallback support for embeddings."""

    def __init__(
        self,
        embedding_provider: str,
        model: str,
        fallback_models: list[str] | None = None,
        **embedding_kwargs: Any,
    ) -> None:
        """Initialize the Memory with fallback support.

        Args:
            embedding_provider: Primary embedding provider
            model: Primary embedding model
            fallback_models: List of fallback models (format: 'provider:model')
            **embedding_kwargs: Additional embedding arguments
        """
        super().__init__(embedding_provider, model, **embedding_kwargs)
        self.fallback_memories: list[Memory] = []

        # Create fallback embedding providers if specified
        if fallback_models:
            for fallback_model in fallback_models:
                try:
                    fallback_provider, fallback_model_name = fallback_model.split(":", 1)
                    # Copy kwargs and update model name
                    fallback_kwargs: dict[str, Any] = embedding_kwargs.copy()
                    fallback_memory = Memory(fallback_provider, fallback_model_name, **fallback_kwargs)
                    self.fallback_memories.append(fallback_memory)
                    logger.info(f"Added fallback embedding model: {fallback_provider}:{fallback_model_name}")
                except (ValueError, ImportError, Exception) as e:
                    logger.warning(f"Failed to initialize fallback embedding provider {fallback_model}: {e}")

    def get_embeddings(self) -> Any:
        """Get embeddings with fallback support.

        Attempts to use the primary embeddings, and if it fails, tries each fallback in order.

        Returns:
            The embeddings provider

        Raises:
            Exception: If all providers fail
        """
        # Try primary provider first
        try:
            return self._embeddings
        except Exception as e:
            if not self.fallback_memories:
                # No fallbacks available, re-raise the original exception
                raise

            logger.warning(f"Primary embedding provider failed: {e.__class__.__name__}: {e}. Trying fallbacks...")

            # Try each fallback in order
            last_error: Exception = e
            for i, fallback_memory in enumerate(self.fallback_memories):
                try:
                    logger.warning(f"Trying fallback embedding provider {i+1}/{len(self.fallback_memories)}")
                    return fallback_memory.get_embeddings()
                except Exception as fallback_error:
                    logger.warning(f"Fallback embedding provider {i+1} failed: {fallback_error.__class__.__name__}: {fallback_error}")
                    last_error = fallback_error

            # All fallbacks failed
            raise Exception(f"All embedding providers failed. Last error: {last_error.__class__.__name__}: {last_error}") from last_error
