import os
from typing import Any

OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

_SUPPORTED_PROVIDERS = {
    "openai",
    "azure_openai",
    "ollama",
    "huggingface",
    "custom",
}


class Memory:
    def __init__(self, embedding_provider: str, model: str, **embdding_kwargs: Any):
        _embeddings = None
        match embedding_provider:
            case "ollama":
                from langchain_community.embeddings import OllamaEmbeddings

                _embeddings = OllamaEmbeddings(
                    model=model,
                    base_url=os.environ["OLLAMA_BASE_URL"],
                    **embdding_kwargs,
                )
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
            case "huggingface":
                from langchain_huggingface import HuggingFaceEmbeddings

                # Specifying the Hugging Face embedding model sentence-transformers/all-MiniLM-L6-v2
                _embeddings = HuggingFaceEmbeddings(model_name=model, **embdding_kwargs)

            case _:
                raise Exception("Embedding not found.")

        self._embeddings = _embeddings

    def get_embeddings(self):
        return self._embeddings
