"""Integration tests for RAG capabilities.

Validates the interplay of ContextManager, VectorStoreWrapper, and
embedding-based similarity search across chunking, ranking, and
context window enforcement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from gpt_researcher.context.compression import (
    ContextCompressor,
    VectorstoreCompressor,
)
from gpt_researcher.vector_store import VectorStoreWrapper
from gpt_researcher.utils.local_llm import LocalHashEmbeddings
from gpt_researcher.prompts import PromptFamily


class _MockEmbeddings(Embeddings):
    """Minimal ``Embeddings`` subclass for use in pydantic-validated tests.

    Returns pre-configured document and query vectors without any real
    embedding computation.
    """

    def __init__(self, doc_vectors, query_vector):
        self._doc_vectors = doc_vectors
        self._query_vector = query_vector
        self.model = "mock-embeddings"

    def embed_documents(self, texts):
        return self._doc_vectors

    def embed_query(self, text):
        if text is None:
            raise TypeError("Cannot embed None query")
        return self._query_vector

    async def aembed_documents(self, texts):
        return self._doc_vectors

    async def aembed_query(self, text):
        return self._query_vector


# =============================================================================
# 1. Chunking & Overlap
# =============================================================================

class TestVectorStoreChunking:
    """VectorStoreWrapper chunking behaviour."""

    def test_chunk_size_not_exceeded(self, sample_documents):
        """Each chunk must stay within ``chunk_size`` (characters)."""
        large_content = "GPT-Researcher is an autonomous agent. " * 10000
        docs = [{"url": "https://ex.com/large", "raw_content": large_content, "title": "Large"}]

        wrapper = VectorStoreWrapper(MagicMock())
        langchain_docs = wrapper._create_langchain_documents(docs)
        chunks = wrapper._split_documents(langchain_docs, chunk_size=1000, chunk_overlap=200)

        for i, chunk in enumerate(chunks):
            assert len(chunk.page_content) <= 1000, (
                f"Chunk {i} has {len(chunk.page_content)} chars, "
                f"exceeds limit of 1000"
            )
        assert len(chunks) > 10, "Large doc should produce many chunks"

    def test_chunk_overlap_preserved(self, sample_documents):
        """Adjacent chunks must share ``overlap`` characters."""
        large_content = "GPT-Researcher is an autonomous agent. " * 10000
        docs = [{"url": "https://ex.com/large", "raw_content": large_content, "title": "Large"}]

        wrapper = VectorStoreWrapper(MagicMock())
        langchain_docs = wrapper._create_langchain_documents(docs)
        chunks = wrapper._split_documents(langchain_docs, chunk_size=1000, chunk_overlap=200)

        for i in range(len(chunks) - 1):
            tail = chunks[i].page_content[-200:]
            head = chunks[i + 1].page_content[:200]
            shared = len(set(tail) & set(head))
            assert shared > 0, (
                f"No character overlap between chunk {i} and {i + 1}"
            )

    def test_split_invoked_on_load(self, sample_documents):
        """``load()`` must flow through splitting."""
        mock_store = MagicMock()
        wrapper = VectorStoreWrapper(mock_store)

        wrapper.load(sample_documents)

        assert mock_store.add_documents.called, "add_documents was not called"
        added = mock_store.add_documents.call_args[0][0]
        assert all(isinstance(d, Document) for d in added)
        assert len(added) >= len(sample_documents), "Documents should have been split"


# =============================================================================
# 2. Cosine-Similarity Ranking
# =============================================================================

class TestCosineSimilarityRanking:
    """Embedding-based similarity ranking and filtering."""

    @pytest.mark.asyncio
    async def test_most_relevant_at_position_zero(self):
        """Doc with highest cosine similarity must appear first."""
        embeddings = _MockEmbeddings(
            doc_vectors=[
                [0.1, 0.0, 0.0, 0.0],
                [0.0, 0.9, 0.0, 0.0],
                [0.0, 0.0, 0.8, 0.0],
                [0.0, 0.0, 0.0, 0.7],
                [0.5, 0.4, 0.0, 0.0],
            ],
            query_vector=[0.0, 1.0, 0.0, 0.0],
        )

        docs = [
            {"url": "https://ex.com/doc0", "raw_content": "Zero",   "title": "Doc0"},
            {"url": "https://ex.com/doc1", "raw_content": "Target", "title": "Doc1"},
            {"url": "https://ex.com/doc2", "raw_content": "Two",    "title": "Doc2"},
            {"url": "https://ex.com/doc3", "raw_content": "Three",  "title": "Doc3"},
            {"url": "https://ex.com/doc4", "raw_content": "Four",   "title": "Doc4"},
        ]

        compressor = ContextCompressor(
            documents=docs,
            embeddings=embeddings,
            embedding_k=10,
            compression_threshold=0,
            similarity_threshold=0.0,
        )
        context = await compressor.async_get_context(query="test", max_results=5)

        first_source = context.split("\n\n")[0] if "\n\n" in context else context
        assert "https://ex.com/doc1" in first_source, (
            f"Doc1 (highest similarity) should appear first, got:\n{first_source}"
        )

    @pytest.mark.asyncio
    async def test_low_similarity_filtered_out(self):
        """Docs below the similarity threshold must be excluded."""
        embeddings = _MockEmbeddings(
            doc_vectors=[
                [0.0, 0.0, 0.0, 1.0],
                [0.0, 0.0, 0.0, 0.9],
            ],
            query_vector=[1.0, 0.0, 0.0, 0.0],
        )

        docs = [
            {"url": "https://ex.com/doc0", "raw_content": "Orthogonal A", "title": "Doc0"},
            {"url": "https://ex.com/doc1", "raw_content": "Orthogonal B", "title": "Doc1"},
        ]

        compressor = ContextCompressor(
            documents=docs,
            embeddings=embeddings,
            embedding_k=10,
            compression_threshold=0,
            similarity_threshold=0.0,
        )
        context = await compressor.async_get_context(query="test", max_results=2)
        assert context == "", (
            "Expected empty context when all docs are below similarity threshold"
        )

    @pytest.mark.asyncio
    async def test_deterministic_ranking_with_local_embeddings(self):
        """``LocalHashEmbeddings`` produces deterministic rankings."""
        ai_doc = {
            "url": "https://ex.com/ai",
            "raw_content": (
                "Artificial intelligence and machine learning are transforming "
                "how we interact with computer systems and technology."
            ),
            "title": "AI",
        }
        cooking_doc = {
            "url": "https://ex.com/cooking",
            "raw_content": (
                "Cooking involves preparing food with heat and various "
                "techniques such as baking and grilling."
            ),
            "title": "Cooking",
        }

        embeddings = LocalHashEmbeddings(dimensions=256)
        compressor = ContextCompressor(
            documents=[cooking_doc, ai_doc],
            embeddings=embeddings,
            embedding_k=10,
            compression_threshold=0,
            similarity_threshold=0.0,
        )
        context = await compressor.async_get_context(
            query="artificial intelligence machine learning", max_results=2
        )

        assert "https://ex.com/ai" in context, (
            "AI doc (topic matches query) should be in the output"
        )


# =============================================================================
# 3. Context Window (Token Truncation)
# =============================================================================

class TestContextWindow:
    """Context window / token-limit enforcement."""

    @pytest.mark.asyncio
    async def test_truncation_by_max_tokens(self):
        """Output must be truncated to ``max_tokens`` when exceeded."""

        embeddings = _MockEmbeddings(
            doc_vectors=[[1.0, 0.0]] * 5,
            query_vector=[1.0, 0.0],
        )

        docs = [
            {"url": f"https://ex.com/doc{i}", "raw_content": "word " * 100, "title": f"Doc{i}"}
            for i in range(5)
        ]

        compressor = ContextCompressor(
            documents=docs,
            embeddings=embeddings,
            max_tokens=10,
            embedding_k=10,
            compression_threshold=0,
        )
        context = await compressor.async_get_context(query="test", max_results=5)

        token_count = len(context.split())
        assert token_count <= 10, (
            f"Context has {token_count} tokens, expected ≤ 10"
        )

    @pytest.mark.asyncio
    async def test_no_truncation_when_under_limit(self):
        """Output must be left intact when under ``max_tokens``."""
        compressor = ContextCompressor(
            documents=[
                {"url": "https://ex.com/short", "raw_content": "Short content.", "title": "Short"}
            ],
            embeddings=MagicMock(),
            max_tokens=1000,
        )
        context = await compressor.async_get_context(query="test", max_results=1)

        token_count = len(context.split())
        assert token_count <= 1000, (
            f"Unexpected truncation: {token_count} tokens"
        )
        assert "Short content" in context

    @pytest.mark.asyncio
    async def test_no_truncation_when_max_tokens_is_none(self):
        """When ``max_tokens`` is None, no truncation should occur."""
        compressor = ContextCompressor(
            documents=[
                {"url": "https://ex.com/doc", "raw_content": "Some longer content here to verify no truncation happens at all when max tokens is none.", "title": "Doc"}
            ],
            embeddings=MagicMock(),
            max_tokens=None,
        )
        context = await compressor.async_get_context(query="test", max_results=2)
        raw = "Some longer content here to verify no truncation happens at all when max tokens is none."
        assert raw in context

    @pytest.mark.asyncio
    async def test_compression_threshold_parameter(self):
        """compression_threshold=0 forces the expensive pipeline path."""
        embeddings = _MockEmbeddings(
            doc_vectors=[[1.0, 0.0]],
            query_vector=[1.0, 0.0],
        )
        doc = {"url": "https://ex.com/d", "raw_content": "Some content here", "title": "D"}
        compressor = ContextCompressor(
            documents=[doc],
            embeddings=embeddings,
            compression_threshold=0,
            similarity_threshold=0.0,
        )
        context = await compressor.async_get_context(query="test", max_results=1)
        assert "https://ex.com/d" in context


# =============================================================================
# 6. ContextManager Full-Path Integration
# =============================================================================

class TestContextManagerFullPath:
    """Full-path integration: ContextManager -> ContextCompressor -> truncation."""

    @pytest.mark.asyncio
    async def test_truncation_via_cfg_max_context_tokens(self, transparent_researcher):
        """cfg.max_context_tokens must be respected through the full path."""
        transparent_researcher.cfg.max_context_tokens = 10

        pages = [
            {"url": f"https://ex.com/doc{i}", "raw_content": "word " * 200, "title": f"Doc{i}"}
            for i in range(5)
        ]

        from gpt_researcher.skills.context_manager import ContextManager
        cm = ContextManager(transparent_researcher)
        context = await cm.get_similar_content_by_query(query="test", pages=pages)

        token_count = len(context.split())
        assert token_count <= 10, (
            f"Context has {token_count} tokens, expected <= 10"
        )

    @pytest.mark.asyncio
    async def test_kwargs_max_tokens_takes_precedence(self, transparent_researcher):
        """kwargs max_tokens must override cfg.max_context_tokens."""
        transparent_researcher.cfg.max_context_tokens = 1000
        transparent_researcher.kwargs["max_tokens"] = 5

        pages = [
            {"url": "https://ex.com/doc", "raw_content": "word " * 200, "title": "Doc"}
        ]

        from gpt_researcher.skills.context_manager import ContextManager
        cm = ContextManager(transparent_researcher)
        context = await cm.get_similar_content_by_query(query="test", pages=pages)

        token_count = len(context.split())
        assert token_count <= 5, (
            f"Context has {token_count} tokens, expected <= 5"
        )
        del transparent_researcher.kwargs["max_tokens"]

    @pytest.mark.asyncio
    async def test_no_max_context_tokens_no_truncation(self, transparent_researcher):
        """When neither cfg nor kwargs has max_tokens, output must be intact."""
        pages = [
            {"url": "https://ex.com/doc", "raw_content": "Short content.", "title": "Doc"}
        ]

        from gpt_researcher.skills.context_manager import ContextManager
        cm = ContextManager(transparent_researcher)
        context = await cm.get_similar_content_by_query(query="test", pages=pages)

        assert "Short content" in context

    @pytest.mark.asyncio
    async def test_compression_threshold_skips_pipeline_for_small_content(self, transparent_researcher):
        """Large compression_threshold must skip expensive pipeline for small content."""
        transparent_researcher.cfg.compression_threshold = 999999

        pages = [
            {"url": "https://ex.com/tiny", "raw_content": "Tiny content.", "title": "Tiny"}
        ]

        from gpt_researcher.skills.context_manager import ContextManager
        cm = ContextManager(transparent_researcher)
        context = await cm.get_similar_content_by_query(query="test", pages=pages)

        assert "Tiny content" in context

    @pytest.mark.asyncio
    async def test_similarity_threshold_from_config(self, transparent_researcher):
        """cfg.similarity_threshold must propagate through ContextManager."""
        transparent_researcher.cfg.similarity_threshold = 0.123

        pages = [
            {"url": "https://ex.com/doc", "raw_content": "Short content.", "title": "Doc"}
        ]

        from gpt_researcher.skills.context_manager import ContextManager
        cm = ContextManager(transparent_researcher)
        context = await cm.get_similar_content_by_query(query="test", pages=pages)

        assert "Short content." in context


# =============================================================================
# 4. Edge Cases
# =============================================================================

class TestEdgeCases:
    """Empty / None inputs."""

    @pytest.mark.asyncio
    async def test_empty_documents_returns_empty(self):
        """Empty document list must yield an empty context string."""
        compressor = ContextCompressor(documents=[], embeddings=MagicMock())
        context = await compressor.async_get_context(query="test")
        assert context == "", f"Expected empty string, got: {context!r}"

    @pytest.mark.asyncio
    async def test_none_query_raises(self):
        """Passing None as query must raise an exception."""

        embeddings = _MockEmbeddings(
            doc_vectors=[[1.0, 0.0]],
            query_vector=[1.0, 0.0],
        )

        compressor = ContextCompressor(
            documents=[
                {"url": "https://ex.com/d", "raw_content": "content", "title": "D"}
            ],
            embeddings=embeddings,
            compression_threshold=0,
        )
        with pytest.raises(Exception):
            await compressor.async_get_context(query=None)

    @pytest.mark.asyncio
    async def test_none_pages_with_context_manager(self, transparent_researcher):
        """Passing None as pages to ``get_similar_content_by_query`` must raise."""
        from gpt_researcher.skills.context_manager import ContextManager
        cm = ContextManager(transparent_researcher)
        with pytest.raises(Exception):
            await cm.get_similar_content_by_query(query="test", pages=None)

    def test_empty_embedding_dimension_raises(self):
        """Zero-dimensional embeddings must raise during inference."""
        with pytest.raises(Exception):
            LocalHashEmbeddings(dimensions=0).embed_query("test")


# =============================================================================
# 5. VectorstoreCompressor Integration
# =============================================================================

class TestVectorstoreCompressor:
    """VectorstoreCompressor passes queries correctly."""

    @pytest.mark.asyncio
    async def test_asimilarity_search_called(self):
        """``async_get_context`` must delegate to ``asimilarity_search``."""
        mock_vs = AsyncMock()
        mock_vs.asimilarity_search.return_value = [
            Document(page_content="Result", metadata={"source": "https://ex.com/r", "title": "R"})
        ]

        mock_wrapper = MagicMock()
        mock_wrapper.asimilarity_search = mock_vs.asimilarity_search

        compressor = VectorstoreCompressor(
            vector_store=mock_wrapper,
            prompt_family=PromptFamily,
        )
        context = await compressor.async_get_context(query="test", max_results=3)

        mock_vs.asimilarity_search.assert_awaited_once_with(
            query="test", k=3, filter=None
        )
        assert "Result" in context

    @pytest.mark.asyncio
    async def test_filter_passed_through(self):
        """Filter dict must be forwarded to ``asimilarity_search``."""
        mock_vs = AsyncMock()
        mock_vs.asimilarity_search.return_value = []

        mock_wrapper = MagicMock()
        mock_wrapper.asimilarity_search = mock_vs.asimilarity_search

        compressor = VectorstoreCompressor(
            vector_store=mock_wrapper,
            filter={"source": "news"},
            prompt_family=PromptFamily,
        )
        _ = await compressor.async_get_context(query="test", max_results=3)

        mock_vs.asimilarity_search.assert_awaited_once_with(
            query="test", k=3, filter={"source": "news"}
        )
