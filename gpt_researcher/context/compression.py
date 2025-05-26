from __future__ import annotations

import asyncio
import logging
import os

from typing import TYPE_CHECKING, Any, Callable

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.base import DocumentCompressorPipeline
from langchain.retrievers.document_compressors.embeddings_filter import EmbeddingsFilter
from langchain.text_splitter import RecursiveCharacterTextSplitter

from gpt_researcher.context.retriever import SearchAPIRetriever, SectionRetriever
from gpt_researcher.memory.embeddings import OPENAI_EMBEDDING_MODEL
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.costs import estimate_embedding_cost
from gpt_researcher.vector_store import VectorStoreWrapper

if TYPE_CHECKING:
    try:
        from langchain_core.documents.base import Document
    except ModuleNotFoundError:
        from langchain.schema import Document

logger = logging.getLogger(__name__)

class VectorstoreCompressor:
    def __init__(
        self,
        vector_store: VectorStoreWrapper,
        max_results: int = 7,
        filter: dict[str, Any] | None = None,
        prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
        **kwargs,
    ):
        self.vector_store: VectorStoreWrapper = vector_store
        self.max_results: int = max_results
        self.filter: dict[str, Any] | None = filter
        self.kwargs: dict[str, Any] = kwargs
        self.prompt_family: type[PromptFamily] | PromptFamily = prompt_family

    async def async_get_context(
        self,
        query: str,
        max_results: int = 5,
        cost_callback: Callable[[float], None] | None = None,
    ) -> str:
        """Get relevant context from vector store.

        Args:
            query (str): The query to retrieve relevant documents from.
            max_results (int): The maximum number of results to return.
            cost_callback (Callable[[float], None]): The callback to call when the cost is estimated.
        """
        results: list[Document] = await self.vector_store.asimilarity_search(query=query, k=max_results, filter=self.filter)
        try:
            if cost_callback is not None:
                cost_callback(estimate_embedding_cost(model=OPENAI_EMBEDDING_MODEL, docs=results))
        except Exception as e:
            print(f"Error in async_get_context: {e.__class__.__name__}: {e}")
            logger.error(f"Error in async_get_context: {e.__class__.__name__}: {e}")
        return self.prompt_family.pretty_print_docs(results, max_results)


class ContextCompressor:
    def __init__(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[float],
        max_results: int = 5,
        prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
        **kwargs,
    ):
        self.max_results: int = max_results
        self.documents: list[dict[str, Any]] = documents
        self.kwargs: dict[str, Any] = kwargs
        self.embeddings: list[float] = embeddings
        self.similarity_threshold: float = float(os.environ.get("SIMILARITY_THRESHOLD", 0.35))
        self.prompt_family: type[PromptFamily] | PromptFamily = prompt_family

    def __get_contextual_retriever(self) -> ContextualCompressionRetriever:
        # Ensure documents have the raw_content key, which is needed by SearchAPIRetriever
        valid_documents: list[dict[str, Any]] = []
        for doc in self.documents:
            if isinstance(doc, dict):
                if "raw_content" not in doc or not doc["raw_content"]:
                    logger.warning(f"Document missing raw_content, adding empty string: {doc}")
                    doc["raw_content"] = ""

                # Only include documents that have non-empty content
                if doc["raw_content"].strip():
                    valid_documents.append(doc)
                else:
                    logger.warning(f"Skipping document with empty raw_content: {doc}")
            else:
                logger.warning(f"Invalid document format (not a dict): {doc.__class__.__name__}")

        # If no valid documents after filtering, return a retriever that will produce no results
        if not valid_documents:
            logger.warning(f"No valid documents with content after filtering. Original count: {len(self.documents)}")
            # Return a retriever that will produce empty results safely
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            pipeline_compressor = DocumentCompressorPipeline(transformers=[splitter])
            base_retriever = SearchAPIRetriever(pages=[])
            return ContextualCompressionRetriever(base_compressor=pipeline_compressor, base_retriever=base_retriever)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        relevance_filter = EmbeddingsFilter(embeddings=self.embeddings, similarity_threshold=self.similarity_threshold)
        pipeline_compressor = DocumentCompressorPipeline(transformers=[splitter, relevance_filter])
        base_retriever = SearchAPIRetriever(pages=valid_documents)
        contextual_retriever = ContextualCompressionRetriever(base_compressor=pipeline_compressor, base_retriever=base_retriever)
        return contextual_retriever

    async def async_get_context(
        self,
        query: str,
        max_results: int = 5,
        cost_callback: Callable[[float], None] | None = None,
    ) -> str:
        # Check if there are any documents to process to prevent downstream errors
        # in LangChain's EmbeddingsFilter when handling empty document lists.
        if not self.documents:
            logger.warning("No documents provided to ContextCompressor.async_get_context")
            return ""

        # Additional check for content quality
        has_content = False
        for doc in self.documents:
            if isinstance(doc, dict) and doc.get("raw_content", "").strip():
                has_content = True
                break

        if not has_content:
            logger.warning("No documents have non-empty raw_content")
            return ""

        compressed_docs: ContextualCompressionRetriever = self.__get_contextual_retriever()
        if cost_callback is not None:
            cost_callback(estimate_embedding_cost(model=OPENAI_EMBEDDING_MODEL, docs=self.documents))

        try:
            relevant_docs: list[Document] = await asyncio.to_thread(compressed_docs.invoke, query)
            return self.prompt_family.pretty_print_docs(relevant_docs, max_results)
        except Exception as e:
            logger.error(f"Error in compress_documents: {e.__class__.__name__}: {e}", exc_info=True)
            # Return empty string in case of errors to avoid crashing the application
            return ""


class WrittenContentCompressor:
    def __init__(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[float],
        similarity_threshold: float,
        **kwargs,
    ):
        self.documents: list[dict[str, Any]] = documents
        self.kwargs: dict[str, Any] = kwargs
        self.embeddings: list[float] = embeddings
        self.similarity_threshold: float = similarity_threshold

    def __get_contextual_retriever(self) -> ContextualCompressionRetriever:
        # Ensure documents have the written_content key needed by SectionRetriever
        valid_documents: list[dict[str, Any]] = []
        for doc in self.documents:
            if isinstance(doc, dict):
                if "written_content" not in doc or not doc["written_content"]:
                    logger.warning(f"Document missing written_content, adding empty string: {doc}")
                    doc["written_content"] = ""

                # Only include documents that have non-empty content
                if doc["written_content"].strip():
                    valid_documents.append(doc)
                else:
                    logger.warning(f"Skipping document with empty written_content: {doc}")
            else:
                logger.warning(f"Invalid document format (not a dict): {doc.__class__.__name__}")

        # If no valid documents after filtering, return a retriever that will produce no results
        if not valid_documents:
            logger.warning(f"No valid documents with content after filtering. Original count: {len(self.documents)}")
            # Return a retriever that will produce empty results safely
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            pipeline_compressor = DocumentCompressorPipeline(transformers=[splitter])
            base_retriever = SectionRetriever(sections=[])
            return ContextualCompressionRetriever(base_compressor=pipeline_compressor, base_retriever=base_retriever)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        relevance_filter = EmbeddingsFilter(embeddings=self.embeddings, similarity_threshold=self.similarity_threshold)
        pipeline_compressor = DocumentCompressorPipeline(transformers=[splitter, relevance_filter])
        base_retriever = SectionRetriever(sections=valid_documents)
        contextual_retriever = ContextualCompressionRetriever(base_compressor=pipeline_compressor, base_retriever=base_retriever)
        return contextual_retriever

    def __pretty_docs_list(self, docs: list[Document], top_n: int) -> list[str]:
        return [f"Title: {d.metadata.get('section_title')}\nContent: {d.page_content}\n" for i, d in enumerate(docs) if i < top_n]

    async def async_get_context(
        self,
        query: str,
        max_results: int = 5,
        cost_callback: Callable[[float], None] | None = None,
    ) -> list[str]:
        # Check if there are any documents to process to prevent downstream errors
        # in LangChain's EmbeddingsFilter when handling empty document lists.
        if not self.documents:
            logger.warning("No documents provided to WrittenContentCompressor.async_get_context")
            return []

        # Additional check for content quality
        has_content = False
        for doc in self.documents:
            if isinstance(doc, dict) and doc.get("written_content", "").strip():
                has_content = True
                break

        if not has_content:
            logger.warning("No documents have non-empty written_content")
            return []

        compressed_docs: ContextualCompressionRetriever = self.__get_contextual_retriever()
        if cost_callback is not None:
            cost_callback(estimate_embedding_cost(model=OPENAI_EMBEDDING_MODEL, docs=self.documents))

        try:
            relevant_docs: list[Document] = await asyncio.to_thread(compressed_docs.invoke, query)
            return self.__pretty_docs_list(relevant_docs, max_results)
        except Exception as e:
            logger.error(f"Error in compress_documents: {e.__class__.__name__}: {e}", exc_info=True)
            # Return empty list in case of errors to avoid crashing the application
            return []
