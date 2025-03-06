from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING, Any

from gpt_researcher.actions.utils import stream_output
from gpt_researcher.context.compression import ContextCompressor, VectorstoreCompressor, WrittenContentCompressor
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import post_retrieval_processing

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher


class ContextManager:
    """Manages context for the researcher agent."""

    def __init__(
        self,
        researcher: GPTResearcher,
    ):
        self.researcher: GPTResearcher = researcher
        self.llm_provider: GenericLLMProvider | None = None

    def _get_llm(self) -> GenericLLMProvider:
        """Get or create an LLM provider instance."""
        if self.llm_provider is None:
            self.llm_provider = GenericLLMProvider(
                self.researcher.cfg.STRATEGIC_LLM,
                temperature=self.researcher.cfg.TEMPERATURE,
                fallback_models=self.researcher.cfg.FALLBACK_MODELS,
                **self.researcher.cfg.llm_kwargs,
            )
        return self.llm_provider

    async def get_similar_content_by_query(
        self,
        query: str,
        pages: list[dict[str, Any]],
    ) -> str:
        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"📚 Getting relevant content based on query: {query}...",
                self.researcher.websocket,
            )

        context_compressor: ContextCompressor = ContextCompressor(
            documents=pages,
            embeddings=self.researcher.memory.get_embeddings(),
        )
        content = await context_compressor.async_get_context(
            query=query,
            max_results=10,
            cost_callback=self.researcher.add_costs,
        )

        # Apply post-retrieval processing if instructions are provided
        if self.researcher.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS and content:
            if self.researcher.cfg.VERBOSE:
                await stream_output(
                    "logs",
                    "post_retrieval_processing",
                    "🔍 Applying post-retrieval processing to content...",
                    self.researcher.websocket,
                )

            provider: GenericLLMProvider = self._get_llm()
            processing_prompt: str = post_retrieval_processing(
                query=query,
                content=content,
                processing_instructions=self.researcher.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS,
            )

            processed_content: str = await provider.get_chat_response(
                messages=[
                    {
                        "role": "system",
                        "content": f"{self.researcher.role}",
                    },
                    {
                        "role": "user",
                        "content": processing_prompt,
                    },
                ],
                stream=False,
            )

            if self.researcher.add_costs:
                from gpt_researcher.utils.costs import estimate_llm_cost

                llm_costs = estimate_llm_cost(
                    processing_prompt,
                    processed_content,
                )
                self.researcher.add_costs(llm_costs)

            return processed_content

        return content

    async def get_similar_content_by_query_with_vectorstore(
        self,
        query: str,
        filter: dict | None = None,
    ) -> str:
        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "fetching_query_format",
                f"📚 Getting relevant content based on query: {query}...",
                self.researcher.websocket,
            )
        if self.researcher.vector_store is None:
            raise ValueError("Vector store is not initialized")
        vectorstore_compressor = VectorstoreCompressor(self.researcher.vector_store, filter=filter)
        content = await vectorstore_compressor.async_get_context(query=query, max_results=8)

        # Apply post-retrieval processing if instructions are provided
        if self.researcher.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS and content:
            if self.researcher.cfg.VERBOSE:
                await stream_output(
                    "logs",
                    "post_retrieval_processing",
                    "🔍 Applying post-retrieval processing to content...",
                    self.researcher.websocket,
                )

            provider: GenericLLMProvider = self._get_llm()
            processing_prompt: str = post_retrieval_processing(
                query=query,
                content=content,
                processing_instructions=self.researcher.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS,
            )

            processed_content: str = await provider.get_chat_response(
                messages=[
                    {
                        "role": "system",
                        "content": f"{self.researcher.role}",
                    },
                    {
                        "role": "user",
                        "content": processing_prompt,
                    },
                ],
                stream=False,
            )

            if self.researcher.add_costs:
                from gpt_researcher.utils.costs import estimate_llm_cost

                llm_costs: float = estimate_llm_cost(
                    processing_prompt,
                    processed_content,
                )
                self.researcher.add_costs(llm_costs)

            return processed_content

        return content

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: list[str],
        written_contents: list[str],
        max_results: int = 10,
    ) -> list[str]:
        all_queries: list[str] = [current_subtopic] + draft_section_titles

        async def process_query(query: str) -> set[str]:
            return set(await self.__get_similar_written_contents_by_query(query, written_contents))

        results: list[set[str]] = await asyncio.gather(*[process_query(query) for query in all_queries])
        relevant_contents: list[str] = list(set().union(*results))[:max_results]

        if relevant_contents and self.researcher.cfg.VERBOSE:
            prettier_contents = "\n".join(relevant_contents)
            await stream_output(
                "logs",
                "relevant_contents_context",
                f"📃 {prettier_contents}",
                self.researcher.websocket,
            )

        return relevant_contents

    async def __get_similar_written_contents_by_query(
        self,
        query: str,
        written_contents: list[str],
        similarity_threshold: float = 0.5,
        max_results: int = 10,
    ) -> list[str]:
        if self.researcher.cfg.VERBOSE:
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
        )
        return await written_content_compressor.async_get_context(
            query=query,
            max_results=max_results,
            cost_callback=self.researcher.add_costs,
        )
