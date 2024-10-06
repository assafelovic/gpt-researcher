from gpt_researcher.context.compression import ContextCompressor
# from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from sqlalchemy.ext.asyncio import create_async_engine

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document

class VectorAgent:
    def __init__(self):
        self.vector_store = None

    async def save_to_vector_store(self, documents):
        # The documents are already Document objects, so we don't need to convert them
        embeddings = OpenAIEmbeddings()
        # self.vector_store = FAISS.from_documents(documents, embeddings)
        pgvector_connection_string = os.environ["PGVECTOR_CONNECTION_STRING"]

        collection_name = "my_docs"

        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=pgvector_connection_string,
            use_jsonb=True
        )

        # for faiss
        # self.vector_store = vector_store.add_documents(documents, ids=[doc.metadata["id"] for doc in documents])

        # Split the documents list into chunks of 100
        for i in range(0, len(documents), 100):
            chunk = documents[i:i+100]
            # Insert the chunk into the vector store
            vector_store.add_documents(chunk, ids=[doc.metadata["id"] for doc in chunk])
            # vector_store.aadd_documents(chunk)

        async_connection_string = pgvector_connection_string.replace("postgresql://", "postgresql+psycopg://")
        
         # Initialize the async engine with the psycopg3 driver
        async_engine = create_async_engine(
            async_connection_string,
            echo=True
        )

        async_vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=async_engine,
            use_jsonb=True
        )

        self.vector_store = async_vector_store
        return self.vector_store

    async def compress_context(self, query, documents):
        embeddings = OpenAIEmbeddings()
        compressor = ContextCompressor(documents, embeddings)
        compressed_context = await compressor.async_get_context(query)
        return compressed_context