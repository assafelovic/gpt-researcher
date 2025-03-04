"""Wrapper for langchain vector store."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

if TYPE_CHECKING:
    from langchain.vectorstores import VectorStore


class VectorStoreWrapper:
    """A Wrapper for LangchainVectorStore to handle GPT-Researcher Document Type."""

    def __init__(
        self,
        vector_store: VectorStore,
    ):
        self.vector_store: VectorStore = vector_store

    def load(
        self,
        documents: list[dict[str, str]],
    ) -> None:
        """Load the documents into vector_store.

        Translate to langchain doc type, split to chunks then load.

        Args:
        ----
            documents: list[dict[str, str]]: The documents to load into the vector store.
        """
        langchain_documents: list[Document] = self._create_langchain_documents(documents)
        splitted_documents: list[Document] = self._split_documents(langchain_documents)
        self.vector_store.add_documents(splitted_documents)

    def _create_langchain_documents(
        self,
        data: list[dict[str, str]],
    ) -> list[Document]:
        """Convert GPT Researcher Document to Langchain Document.

        Args:
        ----
            data: list[dict[str, str]]: The documents to convert to Langchain Document.
                Each dictionary must contain 'raw_content' and 'url' keys.
                'raw_content' contains the text content and 'url' contains the source URL.

        Returns:
        -------
            list[Document]: The Langchain Document.
        """
        return [
            Document(
                page_content=item.get("raw_content", ""),
                metadata={"source": item.get("url", "unknown")},
            )
            for item in data
            if "raw_content" in item  # Only include documents with content
        ]

    def _split_documents(
        self,
        documents: list[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[Document]:
        """Split documents into smaller chunks.

        Args:
        ----
            documents: list[Document]: The documents to split.
            chunk_size: int: The size of the chunks.
            chunk_overlap: int: The overlap of the chunks.

        Returns:
        -------
            list[Document]: The split documents.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return text_splitter.split_documents(documents)

    async def asimilarity_search(
        self,
        query: str,
        k: int,
        filter: dict[str, str] | None = None,
    ) -> list[Document]:
        """Return query by vector store.

        Args:
        ----
            query: str: The query to search for.
            k: int: The number of results to return.
            filter: dict[str, str] | None: The filter to apply to the search.

        Returns:
        -------
            list[Document]: The results of the search.
        """
        results: list[Document] = await self.vector_store.asimilarity_search(
            query=query,
            k=k,
            filter=filter,
        )
        return results
