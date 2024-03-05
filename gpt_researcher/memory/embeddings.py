from langchain.vectorstores import FAISS


class Memory:
    def __init__(self, embedding_provider, **kwargs):

        _embeddings = None
        match embedding_provider:
            case "ollama":
                from langchain_community.embeddings import OllamaEmbeddings
                _embeddings = OllamaEmbeddings(model="llama2")
            case "openai":
                from langchain.embeddings import OpenAIEmbeddings
                _embeddings = OpenAIEmbeddings()
            case "huggingface":
                from langchain_community.embeddings import HuggingFaceEmbeddings
                _embeddings = HuggingFaceEmbeddings()
            case "mixtral":
                from langchain_mistralai import MistralAIEmbeddingscase
                _embeddings = MistralAIEmbeddingscase

            case _:
                raise Exception("Embedding provider not found.")

        self._embeddings = _embeddings

    def get_embeddings(self):
        return self._embeddings
