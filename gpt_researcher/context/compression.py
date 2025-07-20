import os
import asyncio
from typing import Optional
from .retriever import SearchAPIRetriever, SectionRetriever
from langchain.retrievers import (
    ContextualCompressionRetriever,
)
from langchain.retrievers.document_compressors import (
    DocumentCompressorPipeline,
    EmbeddingsFilter,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..vector_store import VectorStoreWrapper
from ..utils.costs import estimate_embedding_cost
from ..memory.embeddings import OPENAI_EMBEDDING_MODEL
from ..prompts import PromptFamily
from langchain_community.vectorstores import FAISS 

class VectorstoreCompressor:
    def __init__(
        self,
        vector_store: VectorStoreWrapper,
        max_results:int = 7,
        filter: Optional[dict] = None,
        prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
        **kwargs,
    ):
        self.vector_store = vector_store
        self.max_results = max_results
        self.filter = filter
        self.kwargs = kwargs
        self.prompt_family = prompt_family

    async def async_get_context(self, query, max_results=5):
        """Get relevant context from vector store with automatic filtering"""

        # Detect vector store backend type
        store_obj = self.vector_store.vector_store  # assumes `VectorStoreWrapper.vector_store` holds the raw LC vector store object

        if isinstance(store_obj, FAISS):
            score_direction = "lower"  # distance metric (e.g., cosine distance)
            threshold = float(os.environ.get("VECTOR_STORE_SIMILARITY_THRESHOLD", 1.0))
        else:
            raise ValueError(f"Unsupported vector store type: {type(store_obj).__name__}. Only FAISS is supported.")

        # Fetch scored results
        results = await self.vector_store.asimilarity_search_with_score(query=query, k=max_results, filter=self.filter)

        # Apply score-based filtering
        if score_direction == "lower":
            filtered = sorted([(doc, score) for doc, score in results if score <= threshold], key=lambda x: x[1])
        else:
            filtered = sorted([(doc, score) for doc, score in results if score >= threshold], key=lambda x: -x[1])

        docs_only = [doc for doc, score in filtered]

      

        return self.prompt_family.pretty_print_docs(docs_only)


class ContextCompressor:
    def __init__(
        self,
        documents,
        embeddings,
        max_results=5,
        prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
        **kwargs,
    ):
        self.max_results = max_results
        self.documents = documents
        self.kwargs = kwargs
        self.embeddings = embeddings
        self.similarity_threshold = float(os.environ.get("SIMILARITY_THRESHOLD", 0.35))
        self.prompt_family = prompt_family

    def __get_contextual_retriever(self):
        #DEBUGGING_STEP 13
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        #DEBUGGING_STEP 14
        relevance_filter = EmbeddingsFilter(embeddings=self.embeddings,
                                            similarity_threshold=self.similarity_threshold)
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[splitter, relevance_filter]
        )
        base_retriever = SearchAPIRetriever(
            pages=self.documents
        )
        contextual_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=base_retriever
        )
        return contextual_retriever

    async def async_get_context(self, query, max_results=5, cost_callback=None):
        #DEBUGGING_STEP 12
        compressed_docs = self.__get_contextual_retriever()
        if cost_callback:
            cost_callback(estimate_embedding_cost(model=OPENAI_EMBEDDING_MODEL, docs=self.documents))
        relevant_docs = await asyncio.to_thread(compressed_docs.invoke, query, **self.kwargs)
        #DEBUGGING_STEP 15
        return self.prompt_family.pretty_print_docs(relevant_docs, max_results)


class WrittenContentCompressor:
    def __init__(self, documents, embeddings, similarity_threshold, **kwargs):
        self.documents = documents
        self.kwargs = kwargs
        self.embeddings = embeddings
        self.similarity_threshold = similarity_threshold

    def __get_contextual_retriever(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        relevance_filter = EmbeddingsFilter(embeddings=self.embeddings,
                                            similarity_threshold=self.similarity_threshold)
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[splitter, relevance_filter]
        )
        base_retriever = SectionRetriever(
            sections=self.documents
        )
        contextual_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=base_retriever
        )
        return contextual_retriever

    def __pretty_docs_list(self, docs, top_n):
        return [f"Title: {d.metadata.get('section_title')}\nContent: {d.page_content}\n" for i, d in enumerate(docs) if i < top_n]

    async def async_get_context(self, query, max_results=5, cost_callback=None):
        compressed_docs = self.__get_contextual_retriever()
        if cost_callback:
            cost_callback(estimate_embedding_cost(model=OPENAI_EMBEDDING_MODEL, docs=self.documents))
        relevant_docs = await asyncio.to_thread(compressed_docs.invoke, query, **self.kwargs)
        return self.__pretty_docs_list(relevant_docs, max_results)
