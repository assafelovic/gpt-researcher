from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

# Here will be all memory logic for holding a meaningful iterative conversation about multiple research tasks
class Memory():
    def __init__(self, **kwargs):
        self._embeddings = OpenAIEmbeddings()

