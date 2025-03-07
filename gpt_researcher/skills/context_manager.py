from __future__ import annotations

import asyncio

from contextlib import suppress
from typing import TYPE_CHECKING, Any, TypeVar

import tiktoken

from litellm.utils import get_max_tokens
from pydantic import BaseModel

from gpt_researcher.actions.utils import stream_output
from gpt_researcher.context.compression import ContextCompressor, VectorstoreCompressor, WrittenContentCompressor
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import post_retrieval_processing

if TYPE_CHECKING:
    from langchain_core.documents.base import Document

    from gpt_researcher.agent import GPTResearcher

# Define a generic type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

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
        content: str = await context_compressor.async_get_context(
            query=query,
            max_results=self.researcher.cfg.MAX_SEARCH_RESULTS_PER_QUERY,
            cost_callback=self.researcher.add_costs,
        )

        # If no content was found, try to find promising links from the pages
        if not content.strip() and pages:
            content = await self._evaluate_and_extract_promising_links(query, pages)

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

    async def _evaluate_and_extract_promising_links(
        self,
        original_query: str,
        pages: list[dict[str, Any]],
        max_depth: int | None = None,
        current_depth: int = 0,
    ) -> str:
        """
        Evaluates the relevance of web pages and extracts promising links for deeper exploration.

        This method is called when standard similarity-based content retrieval fails to find relevant content.
        It uses an LLM to evaluate how relevant each page is to the original research query and identify
        promising links that might contain more relevant information. If a page is highly relevant, its
        content is returned. If not, but promising links are found, those links are followed recursively
        up to the configured MAX_LINK_EXPLORATION_DEPTH.

        This approach allows for more intelligent research that can navigate through web content
        adaptively, following links that are most likely to lead to useful information,
        similar to how a human researcher might explore web content.

        Args:
            original_query: The original research query
            pages: List of page data dictionaries
            max_depth: Maximum recursion depth for link exploration
            current_depth: Current exploration depth

        Returns:
            str: Relevant content found through link exploration
        """
        # Use the configured max depth if none is provided
        if max_depth is None:
            max_depth = self.researcher.cfg.MAX_LINK_EXPLORATION_DEPTH

        if not pages or current_depth >= max_depth:
            return ""

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "evaluating_links",
                "🔍 Evaluating page relevance and looking for promising links...",
                self.researcher.websocket,
            )

        # Create FAST_LLM provider for quick evaluations
        fast_llm = GenericLLMProvider(
            self.researcher.cfg.FAST_LLM,
            temperature=self.researcher.cfg.FAST_LLM_TEMPERATURE,
            fallback_models=self.researcher.cfg.FALLBACK_MODELS,
            **self.researcher.cfg.llm_kwargs,
        )

        max_tokens: int = 32767
        with suppress(Exception):
            max_tokens = get_max_tokens(self.researcher.cfg.FAST_LLM_MODEL) or 32767

        # Calculate token buffer for prompt and other elements (adjust as needed)
        token_buffer: int = 1000  # Reserve tokens for prompt, instructions, etc.
        max_content_tokens: int = max_tokens - token_buffer

        best_links: list[dict[str, Any]] = []
        most_relevant_content: str = ""
        highest_relevance_score: int = 0

        for page in pages:
            # Skip pages without content
            if not page.get("raw_content") or not page.get("href"):
                continue

            # Extract page details
            url: str = page["href"]
            title: str = page["title"]
            content: str = page["raw_content"]

            try:
                encoding = tiktoken.encoding_for_model(self.researcher.cfg.FAST_LLM_MODEL)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")

            content_tokens = encoding.encode(content)

            if len(content_tokens) > max_content_tokens:
                content_tokens: list[int] = content_tokens[:max_content_tokens]
                content: str = encoding.decode(content_tokens)

            content_sample = content

            evaluation_prompt: str = f"""
You are a research assistant evaluating the relevance of a web page to a research query.

ORIGINAL RESEARCH QUERY: {original_query}

WEB PAGE INFORMATION:
Title: {title}
URL: {url}
Content Sample: {content_sample}

TASK:
1. On a scale of 0-10, rate how relevant this content is to the research query
2. Identify up to 3 most promising links on this page that might contain more relevant information about the research query
3. Provide a brief explanation for your rating and link recommendations

FORMAT YOUR RESPONSE AS JSON:
```json
{{
    "relevance_score": <0-10>,
    "explanation": "<brief explanation>",
    "promising_links": [
        {{
            "url": "<url>",
            "description": "<why this link might be useful>"
        }}
    ]
}}
```"""

            try:
                response: str = await fast_llm.get_chat_response(
                    messages=[{"role": "user", "content": evaluation_prompt}],
                    stream=False,
                )

                import json
                import re

                json_match: re.Match[str] | None = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
                json_str: str = response if json_match is None else json_match.group(1)

                evaluation: dict[str, Any] = json.loads(json_str)

                relevance_score: int = evaluation["relevance_score"]
                if relevance_score > highest_relevance_score:
                    highest_relevance_score = relevance_score
                    if relevance_score >= 6:  # Threshold for considering content relevant
                        most_relevant_content = f"Source: {url}\nTitle: {title}\nContent: {content}\n"

                for link_info in evaluation["promising_links"]:
                    link_url: str = link_info["url"]
                    if link_url and link_url not in [link["url"] for link in best_links]:
                        best_links.append(link_info)

                if self.researcher.add_costs:
                    from gpt_researcher.utils.costs import estimate_llm_cost

                    llm_costs: float = estimate_llm_cost(evaluation_prompt, response)
                    self.researcher.add_costs(llm_costs)

            except Exception as e:
                import logging

                logging.warning(f"Error evaluating page '{url}': {e.__class__.__name__}: {e}")

        if most_relevant_content:
            if self.researcher.cfg.VERBOSE:
                await stream_output(
                    "logs",
                    "found_relevant_content",
                    "✅ Found relevant content through LLM evaluation",
                    self.researcher.websocket,
                )
            return most_relevant_content

        if best_links and current_depth < max_depth:
            if self.researcher.cfg.VERBOSE:
                await stream_output(
                    "logs",
                    "exploring_promising_links",
                    f"🔍 Exploring {len(best_links)} promising links for more relevant information...",
                    self.researcher.websocket,
                )
            new_urls: list[str] = [link["url"] for link in best_links[:3]]
            try:
                new_pages: list[dict[str, Any]] = await self.researcher.scraper_manager.browse_urls(new_urls)
                return await self._evaluate_and_extract_promising_links(
                    original_query, new_pages, max_depth, current_depth + 1
                )
            except Exception as e:
                import logging

                logging.warning(f"Error exploring promising links: {e.__class__.__name__}: {e}")

        return most_relevant_content

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

        # If no content was found and we have URLs in the vectorstore, try to find promising links
        if not content.strip() and self.researcher.vector_store:
            # Get the documents from vector store to evaluate
            results: list[Document] = await self.researcher.vector_store.asimilarity_search(
                query=query,
                k=self.researcher.cfg.MAX_SEARCH_RESULTS_PER_QUERY,
                filter=filter,
            )

            # Convert documents to the format expected by _evaluate_and_extract_promising_links
            pages: list[dict[str, Any]] = []
            for doc in results:
                pages.append(
                    {
                        "href": doc.metadata["source"],
                        "title": doc.metadata["title"],
                        "raw_content": doc.page_content,
                    }
                )

            # Use the existing evaluation method
            content = await self._evaluate_and_extract_promising_links(query, pages)

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

                llm_costs: float = estimate_llm_cost(processing_prompt, processed_content)
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

        async def process_query(query: str) -> str:
            return await self.__get_similar_written_contents_by_query(query, written_contents)

        results: list[str] = await asyncio.gather(*[process_query(query) for query in all_queries])
        relevant_contents: set[str] = set().union(*results)
        filtered_relevant_contents: list[str] = list(relevant_contents)[:max_results]

        if relevant_contents and self.researcher.cfg.VERBOSE:
            prettier_contents: str = "\n".join(filtered_relevant_contents)
            await stream_output("logs", "relevant_contents_context", f"📃 {prettier_contents}", self.researcher.websocket)

        return filtered_relevant_contents

    async def __get_similar_written_contents_by_query(
        self,
        query: str,
        written_contents: list[str],
        similarity_threshold: float = 0.5,
        max_results: int = 10,
    ) -> str:
        if self.researcher.cfg.VERBOSE:
            await stream_output("logs", "fetching_relevant_written_content", f"🔎 Getting relevant written content based on query: {query}...", self.researcher.websocket)

        written_content_compressor = WrittenContentCompressor(documents=written_contents, embeddings=self.researcher.memory.get_embeddings(), similarity_threshold=similarity_threshold)
        return await written_content_compressor.async_get_context(query=query, max_results=max_results, cost_callback=self.researcher.add_costs)

