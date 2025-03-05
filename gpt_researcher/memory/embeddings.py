from __future__ import annotations

import os

from typing import Any

from pydantic import SecretStr

OPENAI_EMBEDDING_MODEL: str = os.environ.get(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small",
)


class Memory:
    def __init__(
        self,
        embedding_provider: str,
        model: str,
        **embedding_kwargs: Any,
    ):
        self._setup_embeddings(embedding_provider, model, **embedding_kwargs)

    def _setup_embeddings(
        self,
        embedding_provider: str,
        model: str,
        **embedding_kwargs: Any,
    ):
        _embeddings = None
        match embedding_provider:
            case "custom":
                from langchain_openai import OpenAIEmbeddings

                _api_key: None | SecretStr = (
                    None
                    if os.getenv("OPENAI_API_KEY", "custom") == "custom"
                    else SecretStr(os.getenv("OPENAI_API_KEY", "custom"))
                )
                _embeddings = OpenAIEmbeddings(
                    model=model,
                    api_key=_api_key,
                    organization=os.getenv("OPENAI_ORGANIZATION", "custom"),
                    max_retries=3,
                    timeout=60.0,
                    chunk_size=128,
                    **embedding_kwargs,
                )  # quick fix for lmstudio
            case "openai":
                from langchain_openai import OpenAIEmbeddings

                _embeddings = OpenAIEmbeddings(model=model, **embedding_kwargs)
            case "azure_openai":
                from langchain_openai import AzureOpenAIEmbeddings

                _embeddings = AzureOpenAIEmbeddings(
                    model=model,
                    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],  # type: ignore[arg-type]
                    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],  # type: ignore[arg-type]
                    **embedding_kwargs,
                )
            case "cohere":
                from langchain_cohere import CohereEmbeddings

                _embeddings = CohereEmbeddings(model=model, **embedding_kwargs)
            case "google_vertexai":
                from langchain_google_vertexai import VertexAIEmbeddings

                _embeddings = VertexAIEmbeddings(model=model, **embedding_kwargs)
            case "google_genai":
                from langchain_google_genai import GoogleGenerativeAIEmbeddings

                _embeddings = GoogleGenerativeAIEmbeddings(model=model, **embedding_kwargs)
            case "fireworks":
                from langchain_fireworks import FireworksEmbeddings

                _embeddings = FireworksEmbeddings(model=model, **embedding_kwargs)
            case "ollama":
                from langchain_ollama import OllamaEmbeddings

                _embeddings = OllamaEmbeddings(
                    model=model,
                    base_url=os.environ["OLLAMA_BASE_URL"],
                    **embedding_kwargs,
                )
            case "together":
                from langchain_together import TogetherEmbeddings

                _embeddings = TogetherEmbeddings(model=model, **embedding_kwargs)
            case "mistralai":
                from langchain_mistralai import MistralAIEmbeddings

                _embeddings = MistralAIEmbeddings(model=model, **embedding_kwargs)
            case "huggingface":
                from langchain_huggingface import HuggingFaceEmbeddings

                _embeddings = HuggingFaceEmbeddings(model_name=model, **embedding_kwargs)
            case "nomic":
                from langchain_nomic import NomicEmbeddings

                _embeddings = NomicEmbeddings(model=model, **embedding_kwargs)
            case "voyageai":
                from langchain_voyageai import VoyageAIEmbeddings

                _embeddings = VoyageAIEmbeddings(
                    api_key=SecretStr(os.environ.get("VOYAGE_API_KEY", "")),
                    model=model,
                    **embedding_kwargs,
                )
            case "dashscope":
                from langchain_community.embeddings import DashScopeEmbeddings

                _embeddings = DashScopeEmbeddings(model=model, **embedding_kwargs)
            case "bedrock":
                from langchain_aws.embeddings import BedrockEmbeddings

                _embeddings = BedrockEmbeddings(model_id=model, **embedding_kwargs)
            case _:
                raise Exception(f"Embedding not found: '{embedding_provider}'")

        self._embeddings = _embeddings

    def get_embeddings(self):
        return self._embeddings
