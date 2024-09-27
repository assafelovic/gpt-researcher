from gpt_researcher.context.compression import ContextCompressor
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document

class VectorAgent:
    def __init__(self):
        self.vector_store = None

    async def save_to_vector_store(self, documents):
        # The documents are already Document objects, so we don't need to convert them
        embeddings = OpenAIEmbeddings()
        self.vector_store = FAISS.from_documents(documents, embeddings)
        return self.vector_store

    async def compress_context(self, query, documents):
        embeddings = OpenAIEmbeddings()
        compressor = ContextCompressor(documents, embeddings)
        compressed_context = await compressor.async_get_context(query)
        return compressed_context