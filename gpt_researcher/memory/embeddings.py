from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from gpt_researcher.config import Config
from langchain.embeddings import AzureOpenAIEmbeddings


class Memory:
    def __init__(self, cfg, **kwargs):
        self._embeddings = AzureOpenAIEmbeddings(Config().azure_embedding_model, chunk_size=16)

    def get_embeddings(self):
        return self._embeddings

