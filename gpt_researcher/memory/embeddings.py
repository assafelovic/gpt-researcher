from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

class Memory():
    def __init__(self, **kwargs):
        self._embeddings = OpenAIEmbeddings()

