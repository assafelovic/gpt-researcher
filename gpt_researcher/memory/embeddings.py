import os
from typing import Any

OPENAI_EMBEDDING_MODEL = os.environ.get(
    "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
)

_SUPPORTED_PROVIDERS = {
    "openai",
    "azure_openai",
    "cohere",
    "gigachat",
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
    "aimlapi",
}


class Memory:
    def __init__(self, embedding_provider: str, model: str, **embedding_kwargs: Any):
        _embeddings = None
        
        # Get base URL from kwargs or environment
        base_url = embedding_kwargs.pop('base_url', None) or os.environ.get('EMBEDDING_ENDPOINT')
        
        match embedding_provider:
            case "custom" | "openai":
                from langchain_openai import OpenAIEmbeddings
                
                # For custom endpoints, use a dummy key if none provided
                api_key = os.getenv("OPENAI_API_KEY", "dummy")
                if embedding_provider == "custom" and not base_url:
                    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
                
                _embeddings = OpenAIEmbeddings(
                    model=model,
                    openai_api_key=api_key,
                    openai_api_base=base_url,
                    check_embedding_ctx_length=False,
                    **embedding_kwargs,
                )
            case "azure_openai":
                from langchain_openai import AzureOpenAIEmbeddings

                _embeddings = AzureOpenAIEmbeddings(
                    model=model,
                    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
                    azure_deployment=model,
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
                _embeddings = GoogleGenerativeAIEmbeddings(
                    model=model,
                    **embedding_kwargs,
                )
                
            case "fireworks":
                from langchain_fireworks import FireworksEmbeddings
                _embeddings = FireworksEmbeddings(model=model, **embedding_kwargs)
                
            case "gigachat":
                from langchain_gigachat import GigaChatEmbeddings
                _embeddings = GigaChatEmbeddings(model=model, **embedding_kwargs)
                
            case "ollama":
                from langchain_ollama import OllamaEmbeddings
                # Use provided base_url or fall back to environment variable
                ollama_base = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                _embeddings = OllamaEmbeddings(
                    model=model,
                    base_url=ollama_base,
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
                _embeddings = HuggingFaceEmbeddings(
                    model_name=model, **embedding_kwargs
                )
                
            case "nomic":
                from langchain_nomic import NomicEmbeddings
                _embeddings = NomicEmbeddings(model=model, **embedding_kwargs)
                
            case "voyageai":
                from langchain_voyageai import VoyageAIEmbeddings
                _embeddings = VoyageAIEmbeddings(
                    model=model,
                    voyage_api_key=os.getenv("VOYAGE_API_KEY"),
                    **embedding_kwargs,
                )
                
            case "dashscope":
                from langchain_community.embeddings import DashScopeEmbeddings
                _embeddings = DashScopeEmbeddings(model=model, **embedding_kwargs)
                
            case "bedrock":
                from langchain_aws.embeddings import BedrockEmbeddings
                _embeddings = BedrockEmbeddings(model_id=model, **embedding_kwargs)
                
            case "aimlapi":
                from langchain_openai import OpenAIEmbeddings
                _embeddings = OpenAIEmbeddings(
                    model=model,
                    openai_api_key=os.getenv("OPENAI_API_KEY", "custom"),
                    openai_api_base=base_url or os.getenv("AIMLAPI_BASE_URL"),
                    **embedding_kwargs,
                )
            case _:
                raise Exception("Embedding not found.")

        self._embeddings = _embeddings

    def get_embeddings(self):
        return self._embeddings
