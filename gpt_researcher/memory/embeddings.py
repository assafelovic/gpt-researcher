from langchain_community.vectorstores import FAISS
import os


class Memory:
    def __init__(self, embedding_provider, **kwargs):

        _embeddings = None
        match embedding_provider:
            case "ollama":
                from langchain_community.embeddings import OllamaEmbeddings
                _embeddings = OllamaEmbeddings(model=os.environ["OLLAMA_EMBEDDING_MODEL"], base_url=os.environ["OLLAMA_BASE_URL"])
            case "custom":
                from langchain_openai import OpenAIEmbeddings
                _embeddings = OpenAIEmbeddings(model=os.environ.get("OPENAI_EMBEDDING_MODEL", "custom"),
                                                   openai_api_key=os.environ.get("OPENAI_API_KEY", "custom"), 
                                                   openai_api_base=os.environ.get("OPENAI_BASE_URL", "http://localhost:1234/v1"), #default for lmstudio
                                                   check_embedding_ctx_length=False) #quick fix for lmstudio
            case "openai":
                from langchain_openai import OpenAIEmbeddings
                _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            case "azureopenai":
                from langchain_openai import AzureOpenAIEmbeddings
                _embeddings = AzureOpenAIEmbeddings(deployment=os.environ["AZURE_EMBEDDING_MODEL"], chunk_size=16)
            case "huggingface":
                from langchain.embeddings import HuggingFaceEmbeddings
                _embeddings = HuggingFaceEmbeddings()

            case _:
                raise Exception("Embedding provider not found.")

        self._embeddings = _embeddings

    def get_embeddings(self):
        return self._embeddings
