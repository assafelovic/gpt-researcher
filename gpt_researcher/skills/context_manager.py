"""Context manager skill for GPT Researcher.

This module provides the ContextManager class that handles context
retrieval, compression, and similarity matching for research queries.
"""

import asyncio
from typing import Dict, List, Optional, Set

from ..actions.utils import stream_output
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
    """

    def __init__(self, researcher):
        """Initialize the ContextManager.

        Args:
            researcher: The GPTResearcher instance that owns this manager.
        """
        self.researcher = researcher

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

        context_compressor = ContextCompressor(
            documents=pages,
            embeddings=self.researcher.memory.get_embeddings(),
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
