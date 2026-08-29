"""Context manager skill for GPT Researcher.

This module provides the ContextManager class that handles context
retrieval, compression, and similarity matching for research queries.
"""

import asyncio
from typing import Dict, List, Optional, Set

from ..actions.utils import stream_output
from ..context.concept_diff import ConceptDiffEngine
from ..context.compression import (
    ContextCompressor,
    VectorstoreCompressor,
    WrittenContentCompressor,
)


class ContextManager:
    """Manages context retrieval and compression for research.

    This class handles finding similar content based on queries,
    managing context from various sources, and compressing content
    for efficient processing.

    Attributes:
        researcher: The parent GPTResearcher instance.
        concept_diff_engine: In-memory gatekeeper engine for concept-diff deduplication.
    """

    def __init__(self, researcher):
        """Initialize the ContextManager.

        Args:
            researcher: The GPTResearcher instance that owns this manager.
        """
        self.researcher = researcher
        self.concept_diff_engine: Optional[ConceptDiffEngine] = None
        if getattr(self.researcher.cfg, "enable_concept_diff", False):
            self.concept_diff_engine = ConceptDiffEngine(
                llm_model=getattr(self.researcher.cfg, "fast_llm_model", None),
                llm_provider=getattr(self.researcher.cfg, "fast_llm_provider", None),
                llm_kwargs=getattr(self.researcher.cfg, "llm_kwargs", {}),
                cost_callback=self.researcher.add_costs,
            )

    async def _apply_concept_diff(self, pages: list) -> list:
        """Process scraped pages through the ConceptDiffEngine gatekeeper.

        Args:
            pages: List of raw page content dictionaries.

        Returns:
            List of page content dictionaries with dense diff payloads.
        """
        if not self.concept_diff_engine or not pages:
            return pages

        async def _process_single_page(doc: dict) -> dict:
            if not isinstance(doc, dict):
                return doc
            raw_content = doc.get("raw_content", "") or ""
            if not raw_content or len(raw_content.strip()) < 50:
                return doc

            url = doc.get("url") or doc.get("source") or ""
            title = doc.get("title") or ""
            diff_payload = await self.concept_diff_engine.process_observation(
                raw_text=raw_content,
                source_url=url,
                source_title=title,
            )
            updated_doc = dict(doc)
            updated_doc["raw_content"] = diff_payload
            return updated_doc

        processed_pages = await asyncio.gather(*[_process_single_page(p) for p in pages])
        
        if self.researcher.verbose:
            telemetry = self.concept_diff_engine.get_telemetry()
            await stream_output(
                "logs",
                "concept_diff_reduction",
                f"⚡ Concept-Diff Gatekeeper: {telemetry['word_reduction_pct']}% fluff removed "
                f"({telemetry['total_added_facts']} new facts, {telemetry['total_discarded_facts']} discarded, "
                f"{telemetry['total_conflicts_detected']} conflicts)",
                self.researcher.websocket,
            )

        return processed_pages

    async def get_similar_content_by_query(self, query: str, pages: list) -> str:
        """Get similar content from pages based on the query.

        Args:
            query: The search query to find similar content for.
            pages: List of page content to search through.

        Returns:
            Compressed context string of relevant content.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"📚 Getting relevant content based on query: {query}...",
                self.researcher.websocket,
            )

        # Apply concept-diff gatekeeper if enabled
        if getattr(self.researcher.cfg, "enable_concept_diff", False):
            pages = await self._apply_concept_diff(pages)

        context_compressor = ContextCompressor(
            documents=pages,
            embeddings=self.researcher.memory.get_embeddings(),
            similarity_threshold=getattr(self.researcher.cfg, "similarity_threshold", None),
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )
        return await context_compressor.async_get_context(
            query=query, max_results=10, cost_callback=self.researcher.add_costs
        )

    async def get_similar_content_by_query_with_vectorstore(self, query: str, filter: dict | None) -> str:
        """Get similar content from vectorstore based on the query.

        Args:
            query: The search query to find similar content for.
            filter: Optional filter dictionary for vectorstore queries.

        Returns:
            Compressed context string of relevant content from vectorstore.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_format",
                f" Getting relevant content based on query: {query}...",
                self.researcher.websocket,
                )
        vectorstore_compressor = VectorstoreCompressor(
            self.researcher.vector_store, filter=filter, prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )
        return await vectorstore_compressor.async_get_context(query=query, max_results=8)

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: List[str],
        written_contents: List[Dict],
        max_results: int = 10
    ) -> List[str]:
        """Get similar written contents based on draft section titles.

        Searches for relevant previously written content that matches
        the current subtopic and draft section titles.

        Args:
            current_subtopic: The current subtopic being written.
            draft_section_titles: List of draft section title strings.
            written_contents: List of previously written content dictionaries.
            max_results: Maximum number of results to return.

        Returns:
            List of relevant written content strings.
        """
        all_queries = [current_subtopic] + draft_section_titles

        async def process_query(query: str) -> Set[str]:
            return set(await self.__get_similar_written_contents_by_query(query, written_contents, **self.researcher.kwargs))

        results = await asyncio.gather(*[process_query(query) for query in all_queries])
        relevant_contents = set().union(*results)
        relevant_contents = list(relevant_contents)[:max_results]

        return relevant_contents

    async def __get_similar_written_contents_by_query(
        self,
        query: str,
        written_contents: List[Dict],
        similarity_threshold: float = 0.5,
        max_results: int = 10
    ) -> List[str]:
        """Get similar written contents for a single query.

        Args:
            query: The query to find similar content for.
            written_contents: List of written content dictionaries.
            similarity_threshold: Minimum similarity score threshold.
            max_results: Maximum number of results to return.

        Returns:
            List of similar written content strings.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_relevant_written_content",
                f"🔎 Getting relevant written content based on query: {query}...",
                self.researcher.websocket,
            )

        written_content_compressor = WrittenContentCompressor(
            documents=written_contents,
            embeddings=self.researcher.memory.get_embeddings(),
            similarity_threshold=similarity_threshold,
            **self.researcher.kwargs
        )
        return await written_content_compressor.async_get_context(
            query=query, max_results=max_results, cost_callback=self.researcher.add_costs
        )
