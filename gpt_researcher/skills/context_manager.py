from __future__ import annotations

import asyncio
import logging

from typing import TYPE_CHECKING, Any

from gpt_researcher.actions.utils import stream_output
from gpt_researcher.context.compression import ContextCompressor, VectorstoreCompressor, WrittenContentCompressor
from gpt_researcher.utils.schemas import Subtopic

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher


class ContextManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher: GPTResearcher):
        self.researcher: GPTResearcher = researcher

    async def get_similar_content_by_query(
        self,
        query: Any,
        pages: list[dict[str, Any]],
    ) -> str:
        actual_query_text: str
        if isinstance(query, Subtopic):
            actual_query_text = query.task
        elif isinstance(query, tuple):
            if query and isinstance(query[0], str) and query[0] == "subtopics":
                if len(query) > 1 and isinstance(query[1], list) and query[1] and isinstance(query[1][0], Subtopic):
                    actual_query_text = query[1][0].task
                    if len(query[1]) > 1:
                        logging.warning(
                            f"Query to get_similar_content_by_query was a tuple {query} containing multiple subtopics. Using task from the first subtopic only: '{actual_query_text}'."
                        )
                else:
                    logging.warning(f"Query to get_similar_content_by_query was an unexpected 'subtopics' tuple structure: {query}. Falling back to string conversion.")
                    actual_query_text = str(query)

            elif query and isinstance(query[0], Subtopic):
                actual_query_text = query[0].task
            else:
                logging.warning(f"Query to get_similar_content_by_query was an unexpected tuple: {query}. Falling back to string conversion.")
                actual_query_text = str(query)
        elif isinstance(query, str):
            actual_query_text = query
        else:
            logging.warning(f"Query to get_similar_content_by_query was of unexpected type {type(query)}: {query}. Falling back to string conversion.")
            actual_query_text = str(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"📚 Getting relevant content based on query: {actual_query_text} (Original query type: {type(query)})...",
                self.researcher.websocket,
            )

        context_compressor = ContextCompressor(
            documents=pages,
            embeddings=self.researcher.memory.get_embeddings(),
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )
        return await context_compressor.async_get_context(
            query=actual_query_text,
            max_results=10,
            cost_callback=self.researcher.add_costs,
        )

    async def get_similar_content_by_query_with_vectorstore(
        self,
        query: str,
        filter: dict[str, Any],
    ) -> str:
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_format",
                f" Getting relevant content based on query: {query}...",
                self.researcher.websocket,
            )
        vectorstore_compressor = VectorstoreCompressor(
            self.researcher.vector_store,
            filter=filter,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs,
        )
        return await vectorstore_compressor.async_get_context(query=query, max_results=8)

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: list[str],
        written_contents: list[dict[str, Any]],
        max_results: int = 10,
    ) -> list[str]:
        all_queries: list[str] = [current_subtopic] + draft_section_titles

        async def process_query(query: str) -> set[str]:
            return set(await self.__get_similar_written_contents_by_query(query, written_contents, **self.researcher.kwargs))

        results: list[set[str]] = await asyncio.gather(*[process_query(query) for query in all_queries])
        relevant_contents_set: set[str] = set().union(*results)
        relevant_contents: list[str] = list(relevant_contents_set)[:max_results]

        if relevant_contents and self.researcher.verbose:
            prettier_contents: str = "\n".join(relevant_contents)
            await stream_output("logs", "relevant_contents_context", f"📃 {prettier_contents}", self.researcher.websocket)

        return relevant_contents

    async def __get_similar_written_contents_by_query(
        self,
        query: str,
        written_contents: list[dict[str, Any]],
        similarity_threshold: float = 0.5,
        max_results: int = 10,
    ) -> list[str]:
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
            **self.researcher.kwargs,
        )
        return await written_content_compressor.async_get_context(query=query, max_results=max_results, cost_callback=self.researcher.add_costs)
