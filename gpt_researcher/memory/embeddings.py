import os
from typing import Any

OPENAI_EMBEDDING_MODEL = os.environ.get(
    "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
)

_SUPPORTED_PROVIDERS = {
    "openai",
    "azure_openai",
    "cohere",
    "google_vertexai",
    "google_genai",
    "fireworks",
    "ollama",
    "together",
    "mistralai",
    "huggingface",
    "nomic",
    "voyageai",
    "dashscope",
    "custom",
    "bedrock",
}


class Memory:
    def __init__(self, embedding_provider: str, model: str, **embdding_kwargs: Any):
        _embeddings = None
        match embedding_provider:
            case "custom":
                from langchain_openai import OpenAIEmbeddings

                _embeddings = OpenAIEmbeddings(
                    model=model,
                    openai_api_key=os.getenv("OPENAI_API_KEY", "custom"),
                    openai_api_base=os.getenv(
                        "OPENAI_BASE_URL", "http://localhost:1234/v1"
                    ),  # default for lmstudio
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
                    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
                    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
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

                _embeddings = GoogleGenerativeAIEmbeddings(
                    model=model, **embdding_kwargs
                )
            case "fireworks":
                from langchain_fireworks import FireworksEmbeddings

                _embeddings = FireworksEmbeddings(model=model, **embdding_kwargs)
            case "ollama":
                from langchain_ollama import OllamaEmbeddings

                _embeddings = OllamaEmbeddings(
                    model=model,
                    base_url=os.environ["OLLAMA_BASE_URL"],
                    **embdding_kwargs,
                )
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

                _embeddings = VoyageAIEmbeddings(
                    voyage_api_key=os.environ["VOYAGE_API_KEY"],
                    model=model,
                    **embdding_kwargs,
                )
            case "dashscope":
                from langchain_community.embeddings import DashScopeEmbeddings

                _embeddings = DashScopeEmbeddings(model=model, **embdding_kwargs)
            case "bedrock":
                from langchain_aws.embeddings import BedrockEmbeddings

                _embeddings = BedrockEmbeddings(model_id=model, **embdding_kwargs)
            case _:
                raise Exception("Embedding not found.")

        self._embeddings = _embeddings

    def get_embeddings(self):
        return self._embeddings
