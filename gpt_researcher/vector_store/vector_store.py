"""Wrapper for langchain vector store."""
from __future__ import annotations

from typing import Any

from langchain.docstore.document import Document
from langchain.vectorstores import VectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

class VectorStoreWrapper:
    """A Wrapper for LangchainVectorStore to handle GPT-Researcher Document Type."""
    def __init__(self, vector_store: VectorStore):
        self.vector_store: VectorStore = vector_store

    def load(self, documents: list[dict[str, str]]) -> None:
        """Load the documents into vector_store.

        Translate to langchain doc type, split to chunks then load.
        """
        langchain_documents: list[Document] = self._create_langchain_documents(documents)
        splitted_documents: list[Document] = self._split_documents(langchain_documents)
        self.vector_store.add_documents(splitted_documents)

    def _create_langchain_documents(self, data: list[dict[str, str]]) -> list[Document]:
        """Convert GPT Researcher Document to Langchain Document"""
        return [
            Document(page_content=item["raw_content"], metadata={"source": item["url"]})
            for item in data
        ]

    def _split_documents(
        self,
        documents: list[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[Document]:
        """Split documents into smaller chunks."""
        text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return text_splitter.split_documents(documents)

    async def asimilarity_search(
        self,
        query: str,
        k: int,
        filter: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Return query by vector store"""
        results: list[Document] = await self.vector_store.asimilarity_search(query=query, k=k, filter=filter)
        return results
