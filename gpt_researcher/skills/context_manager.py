import asyncio
from typing import List, Dict, Optional, Set

from ..context.compression import ContextCompressor, WrittenContentCompressor, VectorstoreCompressor
from ..actions.utils import stream_output


class ContextManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher):
        self.researcher = researcher

    async def get_similar_content_by_query(self, query, pages):
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"📚 Getting relevant content based on query: {query}...",
                self.researcher.websocket,
            )

        context_compressor = ContextCompressor(
            documents=pages, embeddings=self.researcher.memory.get_embeddings()
        )
        return await context_compressor.async_get_context(
            query=query, max_results=10, cost_callback=self.researcher.add_costs
        )
        
    async def get_similar_content_by_query_with_vectorstore(self, query, filter): 
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_format",
                f" Getting relevant content based on query: {query}...",
                self.researcher.websocket,
                )
        vectorstore_compressor = VectorstoreCompressor(self.researcher.vector_store, filter)
        return await vectorstore_compressor.async_get_context(query=query, max_results=8)
    
    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: List[str],
        written_contents: List[Dict],
        max_results: int = 10
    ) -> List[str]:
        all_queries = [current_subtopic] + draft_section_titles

        async def process_query(query: str) -> Set[str]:
            return set(await self.__get_similar_written_contents_by_query(query, written_contents))

        results = await asyncio.gather(*[process_query(query) for query in all_queries])
        relevant_contents = set().union(*results)
        relevant_contents = list(relevant_contents)[:max_results]

        return relevant_contents

    async def __get_similar_written_contents_by_query(self,
                                                      query: str,
                                                      written_contents: List[Dict],
                                                      similarity_threshold: float = 0.5,
                                                      max_results: int = 10
                                                      ) -> List[str]:
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
            similarity_threshold=similarity_threshold
        )
        return await written_content_compressor.async_get_context(
            query=query, max_results=max_results, cost_callback=self.researcher.add_costs
        )
