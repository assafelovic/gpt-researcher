from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Any, Callable

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.base import DocumentCompressorPipeline
from langchain.retrievers.document_compressors.embeddings_filter import EmbeddingsFilter
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from gpt_researcher.context.retriever import SearchAPIRetriever, SectionRetriever
from gpt_researcher.memory.embeddings import OPENAI_EMBEDDING_MODEL
from gpt_researcher.utils.costs import estimate_embedding_cost

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

    from gpt_researcher.vector_store import VectorStoreWrapper


class VectorstoreCompressor:
    def __init__(
        self,
        vector_store: VectorStoreWrapper,
        max_results: int = 7,
        filter: dict[str, Any] | None = None,
        **kwargs,
    ):
        self.vector_store: VectorStoreWrapper = vector_store
        self.max_results: int = max_results
        self.filter: dict[str, Any] | None = filter
        self.kwargs: dict[str, Any] = kwargs

    def __pretty_print_docs(self, docs):
        return "\n".join(
            f"Source: {d.metadata.get('source')}\nTitle: {d.metadata.get('title')}\nContent: {d.page_content}\n"
            for d in docs
        )

    async def async_get_context(
        self,
        query: str,
        max_results: int = 5,
    ):
        """Get relevant context from vector store."""
        results = await self.vector_store.asimilarity_search(
            query=query,
            k=max_results,
            filter=self.filter,
        )
        return self.__pretty_print_docs(results)


class ContextCompressor:
    def __init__(
        self,
        documents: list,
        embeddings: Embeddings,
        max_results: int = 5,
        similarity_threshold: float = 0.35,
        **kwargs,
    ):
        self.max_results: int = max_results
        self.documents: list = documents
        self.kwargs: dict[str, Any] = kwargs
        self.embeddings: Embeddings = embeddings
        self.similarity_threshold: float = float(
            os.environ.get("SIMILARITY_THRESHOLD", similarity_threshold)
        )

    def __get_contextual_retriever(self):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )
        relevance_filter = EmbeddingsFilter(
            embeddings=self.embeddings,
            similarity_threshold=self.similarity_threshold,
        )
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[
                splitter,
                relevance_filter,
            ],
        )
        base_retriever = SearchAPIRetriever(pages=self.documents)  # pyright: ignore[reportCallIssue]

        return ContextualCompressionRetriever(
            base_compressor=pipeline_compressor,
            base_retriever=base_retriever,
        )

    def __pretty_print_docs(
        self,
        docs: list,
        top_n: int,
    ):
        return "\n".join(
            f"Source: {d.metadata.get('source')}\nTitle: {d.metadata.get('title')}\nContent: {d.page_content}\n"
            for i, d in enumerate(docs)
            if i < top_n
        )

    async def async_get_context(
        self,
        query: str,
        max_results: int = 5,
        cost_callback: Callable[[float], None] | None = None,
    ):
        compressed_docs = self.__get_contextual_retriever()
        if cost_callback:
            cost_callback(
                estimate_embedding_cost(model=OPENAI_EMBEDDING_MODEL, docs=self.documents)
            )
        relevant_docs = await asyncio.to_thread(compressed_docs.invoke, query)
        return self.__pretty_print_docs(relevant_docs, max_results)


class WrittenContentCompressor:
    def __init__(
        self,
        documents: list,
        embeddings: Embeddings,
        similarity_threshold: float = 0.35,
        **kwargs,
    ):
        self.documents: list = documents
        self.kwargs: dict[str, Any] = kwargs
        self.embeddings: Embeddings = embeddings
        self.similarity_threshold: float = float(similarity_threshold)

    def __get_contextual_retriever(self):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )
        relevance_filter = EmbeddingsFilter(
            embeddings=self.embeddings,
            similarity_threshold=self.similarity_threshold,
        )
        pipeline_compressor = DocumentCompressorPipeline(transformers=[splitter, relevance_filter])
        base_retriever = SectionRetriever(sections=self.documents)  # pyright: ignore[reportCallIssue]
        contextual_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor,
            base_retriever=base_retriever,
        )
        return contextual_retriever

    def __pretty_docs_list(
        self,
        docs: list[Document],
        top_n: int,
    ) -> list[str]:
        return [
            f"Title: {d.metadata.get('section_title')}\nContent: {d.page_content}\n"
            for i, d in enumerate(docs)
            if i < top_n
        ]

    async def async_get_context(
        self,
        query: str,
        max_results: int = 5,
        cost_callback: Callable[[float], None] | None = None,
    ) -> list[str]:
        compressed_docs: ContextualCompressionRetriever = self.__get_contextual_retriever()
        if cost_callback is not None:
            cost_callback(
                estimate_embedding_cost(model=OPENAI_EMBEDDING_MODEL, docs=self.documents)
            )
        relevant_docs: list = await asyncio.to_thread(compressed_docs.invoke, query)
        return self.__pretty_docs_list(
            relevant_docs,
            max_results,
        )
