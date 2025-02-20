from __future__ import annotations

import asyncio
import logging
import random

from typing import TYPE_CHECKING, Any, Callable

import json_repair

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from litellm.utils import get_max_tokens

from gpt_researcher.actions import stream_output
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.document.langchain_document import LangChainDocumentLoader
from gpt_researcher.document.online_document import OnlineDocumentLoader
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import generate_search_queries_prompt
from gpt_researcher.utils.schemas import ReportSource, ReportType

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher
    from gpt_researcher.config import Config
    from gpt_researcher.utils.logging_config import JSONResearchHandler


logger = logging.getLogger(__name__)


class ResearchConductor:
    """Manages and coordinates the research process."""

    def __init__(self, researcher: GPTResearcher):
        self.researcher: GPTResearcher = researcher
        self.logger: logging.Logger = logging.getLogger("research")
        self.json_handler: JSONResearchHandler | None = getattr(self.logger, "json_handler", None)
        self.llm_provider: GenericLLMProvider | None = None

    def _get_llm(
        self,
        model: str,
        provider: str,
        temperature: float,
    ) -> GenericLLMProvider:
        """Get or create an LLM provider instance.

        Args:
            model: The model to use
            provider: The LLM provider to use
            temperature: The temperature to use for generation

        Returns:
            The LLM provider instance
        """
        if self.llm_provider is None:
            self.llm_provider = GenericLLMProvider.from_provider(
                provider,
                model=model,
                temperature=temperature,
            )
        return self.llm_provider

    async def plan_research(self, query: str) -> list[str]:
        self.logger.info(f"Planning research for query: {query}")

        await stream_output(
            "logs",
            "planning_research",
            f"🌐 Browsing the web to learn more about the task: {query}...",
            self.researcher.websocket,
        )

        search_results: list[dict[str, Any]] = await get_search_results(
            query,
            self.researcher.retrievers[0],
        )
        self.logger.info(f"Initial search results obtained: {len(search_results)} results")

        await stream_output(
            "logs",
            "planning_research",
            "🤔 Planning the research strategy and subtasks...",
            self.researcher.websocket,
        )

        outline = await generate_sub_queries(
            query=query,
            context=search_results,
            research_config=self.researcher.research_config,
            parent_query=self.researcher.parent_query,
            report_type=self.researcher.report_type,
            cost_callback=self.researcher.add_costs,
        )
        self.logger.info(f"Research outline planned: {outline}")
        return outline

    async def conduct_research(self) -> list[str]:
        """Runs the GPT Researcher to conduct research."""
        if self.json_handler is not None:
            self.json_handler.update_content("query", self.researcher.query)

        self.logger.info(f"Starting research for query: {self.researcher.query}")

        # Reset visited_urls and source_urls at the start of each research task
        self.researcher.visited_urls.clear()
        research_data: list[str] = []

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "starting_research",
                f"🔍 Starting the research task for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "agent_generated",
                self.researcher.agent or "🤖 I am an AI Researcher, here to help you with your queries...",
                self.researcher.websocket,
            )

        # Research for relevant sources based on source types below
        if self.researcher.source_urls:
            self.logger.info("Using provided source URLs")
            research_data = [await self._get_context_by_urls(self.researcher.source_urls)]
            if research_data[0] and len(research_data[0]) == 0 and self.researcher.verbose:
                await stream_output(
                    "logs",
                    "answering_from_memory",
                    "🧐 I was unable to find relevant context in the provided sources...",
                    self.researcher.websocket,
                )
            if self.researcher.complement_source_urls:
                self.logger.info("Complementing with web search")
                additional_research = await self._get_context_by_web_search(self.researcher.query)
                research_data += " ".join(additional_research)

        elif self.researcher.research_config.REPORT_SOURCE == ReportSource.WEB.value:
            self.logger.info("Using web search")
            research_data = [await self._get_context_by_web_search(self.researcher.query)]

        elif self.researcher.research_config.REPORT_SOURCE == ReportSource.LOCAL.value:
            document_data = await DocumentLoader(self.researcher.research_config.DOC_PATH).load()
            if self.researcher.vector_store is not None:
                self.researcher.vector_store.load(document_data)

            research_data = [
                await self._get_context_by_web_search(
                    self.researcher.query,
                    document_data,
                )
            ]

        # Hybrid search including both local documents and web sources
        elif self.researcher.research_config.REPORT_SOURCE == ReportSource.HYBRID.value:
            if self.researcher.document_urls:
                document_data = await OnlineDocumentLoader(self.researcher.document_urls).load()
            else:
                document_data = await DocumentLoader(self.researcher.research_config.DOC_PATH).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)
            docs_context = await self._get_context_by_web_search(
                self.researcher.query,
                document_data,
            )
            web_context = await self._get_context_by_web_search(self.researcher.query)
            research_data = [f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"]

        elif self.researcher.research_config.REPORT_SOURCE == ReportSource.LANGCHAIN_DOCUMENTS.value:
            self.logger.info("Using LangChain documents")
            lang_docs = [Document(**doc) for doc in self.researcher.documents]
            langchain_documents_data = await LangChainDocumentLoader(lang_docs).load()
            if self.researcher.vector_store is not None:
                self.researcher.vector_store.load(langchain_documents_data)
            research_data = [
                await self._get_context_by_web_search(
                    self.researcher.query,
                    langchain_documents_data,
                )
            ]

        elif self.researcher.research_config.OUTPUT_FORMAT == ReportSource.LANGCHAIN_VECTOR_STORE.value:
            research_data = await self._get_context_by_vectorstore(
                self.researcher.query,
                self.researcher.vector_store_filter,
            )

        # Rank and curate the sources
        self.researcher.context.extend(research_data)
        if self.researcher.research_config.CURATE_SOURCES:
            self.logger.info("Curating sources")
            self.researcher.context = await self.researcher.source_curator.curate_sources(research_data)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_step_finalized",
                f"Finalized research step.\n💸 Total Research Costs: ${self.researcher.get_costs()}",
                self.researcher.websocket,
            )
            if self.json_handler is not None:
                self.json_handler.update_content("costs", self.researcher.get_costs())
                self.json_handler.update_content("context", self.researcher.context)

        self.logger.info(f"Research completed. Context size: {len(str(self.researcher.context))}")
        return self.researcher.context

    async def _get_context_by_urls(
        self,
        urls: list[str],
    ) -> str:
        """Scrapes and compresses the context from the given urls."""
        self.logger.info(f"Getting context from URLs: {urls}")

        new_search_urls: list[str] = await self._get_new_urls(set(urls))
        self.logger.info(f"New URLs to process: {new_search_urls}")

        scraped_content: tuple[list[dict[str, Any]], list[dict[str, Any]]] = await self.researcher.scraper_manager.browse_urls(new_search_urls)
        self.logger.info(f"Scraped content from {len(scraped_content[0])} URLs")

        if self.researcher.vector_store is not None:
            self.logger.info("Loading content into vector store")
            self.researcher.vector_store.load(scraped_content[0])

        context = await self.researcher.context_manager.get_similar_content_by_query(
            self.researcher.query,
            scraped_content[0],
        )
        self.logger.info(f"Generated context length: {len(context)}")
        return context

    # Add logging to other methods similarly...

    async def _get_context_by_vectorstore(
        self,
        query: str,
        vector_store_filter: dict[str, Any] | None = None,
    ) -> list[str]:
        """Generates the context for the research task by searching the vectorstore.

        Args:
            query: The query to search for.
            filter: The filter to apply to the vectorstore.

        Returns:
            context: List of context.
        """
        context: list[str] = []
        # Generate Sub-Queries including original query
        sub_queries: list[str] = await self.plan_research(query)
        # If this is not part of a sub researcher, add original query to research for better results
        if self.researcher.report_type != ReportType.SubtopicReport:
            sub_queries.append(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️  I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                True,
                {"queries": sub_queries},
            )

        # Using asyncio.gather to process the sub_queries asynchronously
        context = await asyncio.gather(
            *[
                self._process_sub_query_with_vectorstore(
                    sub_query,
                    vector_store_filter,
                )
                for sub_query in sub_queries
            ]
        )
        return context

    async def _get_context_by_web_search(
        self,
        query: str,
        scraped_data: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generates the context for the research task by searching the query and scraping the results.

        Args:
            query: The query to search for.
            scraped_data: List of scraped data.

        Returns:
            context: List of context.
        """
        scraped_data = [] if scraped_data is None else scraped_data
        self.logger.info(f"Starting web search for query: {query}")

        # Generate Sub-Queries including original query
        sub_queries: list[str] = await self.plan_research(query)
        self.logger.info(f"Generated sub-queries: {sub_queries}")

        # If this is not part of a sub researcher, add original query to research for better results
        if self.researcher.report_type != ReportType.SubtopicReport:
            sub_queries.append(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️ I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                True,
                {"queries": sub_queries},
            )

        # Using asyncio.gather to process the sub_queries asynchronously
        try:
            context = await asyncio.gather(*[self._process_sub_query(sub_query, scraped_data) for sub_query in sub_queries])
            self.logger.info(f"Gathered context from {len(context)} sub-queries")
            # Filter out empty results and join the context
            context = [c for c in context if c.strip()]
            if context:
                combined_context = " ".join(context)
                self.logger.info(f"Combined context size: {len(combined_context)}")
                return combined_context
        except Exception as e:
            self.logger.exception(f"Error during web search: {e.__class__.__name__}: {e}")
        return ""

    async def _process_sub_query(
        self,
        sub_query: str,
        scraped_data: list[dict[str, Any]] | None = None,
    ) -> str:
        """Takes in a sub query and scrapes urls based on it and gathers context."""
        scraped_data = [] if scraped_data is None else scraped_data
        if self.json_handler is not None:
            self.json_handler.log_event(
                "sub_query",
                {
                    "query": sub_query,
                    "scraped_data_size": len(scraped_data),
                },
            )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.researcher.websocket,
            )

        try:
            if not scraped_data:
                scraped_data = await self._scrape_data_by_urls(sub_query)
                self.logger.info(f"Scraped data size: {len(scraped_data)}")

            content = await self.researcher.context_manager.get_similar_content_by_query(
                sub_query,
                scraped_data,
            )
            self.logger.info(f"Content found for sub-query: {len(str(content)) if content else 0} chars")

            if content and content.strip():
                await stream_output(
                    "logs",
                    "subquery_context_window",
                    f"📃 {content}",
                    self.researcher.websocket,
                )
                if self.researcher.verbose and self.json_handler is not None:
                    self.json_handler.log_event(
                        "content_found",
                        {
                            "sub_query": sub_query,
                            "content_size": len(content),
                        },
                    )
            elif self.researcher.verbose:
                await stream_output(
                    "logs",
                    "subquery_context_not_found",
                    f"🤷 No content found for '{sub_query}'...",
                    self.researcher.websocket,
                )
            return content
        except Exception as e:
            self.logger.exception(f"Error processing sub-query {sub_query}: {e.__class__.__name__}: {e}")
            return ""

    async def _process_sub_query_with_vectorstore(
        self,
        sub_query: str,
        sub_filter: dict[str, Any] | None = None,
    ) -> str:
        """Takes in a sub query and gathers context from the user provided vector store.

        Args:
            sub_query (str): The sub-query generated from the original query

        Returns:
            str: The context gathered from search
        """
        sub_filter = {} if sub_filter is None else sub_filter
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_with_vectorstore_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.researcher.websocket,
            )

        content: str = await self.researcher.context_manager.get_similar_content_by_query_with_vectorstore(
            sub_query,
            sub_filter,
        )

        self.logger.debug(f"Content found for sub-query: {len(str(content)) if content else 0} chars")
        if not self.researcher.verbose:
            return content

        if content and content.strip():
            await stream_output(
                "logs",
                "subquery_context_window",
                f"📃 {content}",
                self.researcher.websocket,
            )
        else:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 No content found for '{sub_query}'...",
                self.researcher.websocket,
            )
        return content

    async def _get_new_urls(
        self,
        url_set_input: set[str],
    ) -> list[str]:
        """Gets the new urls from the given url set.

        Args:
            url_set_input (set[str]): The url set to get the new urls from

        Returns:
            list[str]: The new urls from the given url set.
        """

        new_urls: list[str] = []
        for url in url_set_input:
            if url in self.researcher.visited_urls:
                continue
            self.researcher.visited_urls.add(url)
            new_urls.append(url)
            if not self.researcher.verbose:
                continue
            await stream_output(
                "logs",
                "added_source_url",
                f"✅ Added source url to research: {url}\n",
                self.researcher.websocket,
                True,
                {"url": url},
            )

        return new_urls

    async def _search_relevant_source_urls(
        self,
        query: str,
    ) -> list[str]:
        """For non-langchain retrievers, search for relevant source urls."""
        new_search_urls: set[str] = set()

        # Iterate through all retrievers
        for retriever_class in self.researcher.retrievers:
            if not issubclass(retriever_class, BaseRetriever):
                continue

            # Instantiate the retriever with the sub-query
            retriever: BaseRetriever = retriever_class(query)  # type: ignore

            # Perform the search using the current retriever
            search_results: list[Document] | None = await retriever.aget_relevant_documents(query, max_results=self.researcher.research_config.MAX_SEARCH_RESULTS_PER_QUERY)
            if search_results is None:
                continue

            # Collect new URLs from search results
            search_urls: list[str] = [str(webpage.metadata.get("source", webpage.metadata.get("href", ""))) for webpage in search_results]
            new_search_urls.update(search_urls)

        # Get unique URLs
        new_search_urls_list: list[str] = await self._get_new_urls(new_search_urls)
        random.shuffle(new_search_urls_list)

        return new_search_urls_list

    async def _scrape_data_by_urls(
        self,
        sub_query: str,
    ) -> list[dict[str, Any]]:
        """Runs a sub-query across multiple retrievers and scrapes the resulting URLs.

        Args:
            sub_query (str): The sub-query to search for.

        Returns:
            list: A list of scraped content results.
        """
        new_search_urls: list[str] = await self._search_relevant_source_urls(sub_query)

        # Log the research process if verbose mode is on
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "researching",
                "🤔 Researching for relevant information across multiple sources...\n",
                self.researcher.websocket,
            )

        # Scrape the new URLs
        scraped_content: tuple[list[dict[str, Any]], list[dict[str, Any]]] = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store is not None:
            self.researcher.vector_store.load(scraped_content[0])

        return scraped_content[0]


async def get_search_results(
    query: str,
    retriever: type,
) -> list[dict[str, Any]]:
    """Get web search results for a given query.

    Args:
        query: The search query
        retriever: The retriever class to instantiate

    Returns:
        A list of search results
    """
    # Instantiate the retriever with the query
    retriever_instance: BaseRetriever = retriever(query)

    # Get documents using Langchain's retriever interface
    documents: list[Document] = await retriever_instance.aget_relevant_documents(query)

    # Convert Langchain documents to the expected format
    return [
        {
            "href": doc.metadata.get("source", ""),
            "title": doc.metadata.get("title", ""),
            "raw_content": doc.page_content,
        }
        for doc in documents
    ]


async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: ReportType,
    context: list[dict[str, Any]],
    research_config: Config,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str]:
    """Generate sub-queries using the specified LLM model.

    Args:
        query: The original query
        parent_query: The parent query
        report_type: The type of report
        max_iterations: Maximum number of research iterations
        context: Search results context
        cfg: Configuration object
        cost_callback: Callback for cost calculation

    Returns:
        A list of sub-queries
    """
    llm_queries_prompt: str = generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=research_config.MAX_ITERATIONS or 1,
        context=context,
    )

    strategic_token_limit = get_max_tokens(research_config.STRATEGIC_LLM_MODEL)  # pyright: ignore[reportArgumentType]
    try:
        provider = GenericLLMProvider.from_provider(
            research_config.STRATEGIC_LLM_PROVIDER,
            model=research_config.STRATEGIC_LLM_MODEL,
            temperature=research_config.TEMPERATURE,
            max_tokens=strategic_token_limit,
            **research_config.llm_kwargs,
        )
        response = await provider.get_chat_response(
            messages=[{"role": "user", "content": llm_queries_prompt}],
            stream=False,
        )
    except Exception as e:
        logger.warning(f"Error with strategic LLM: {e.__class__.__name__}: {e}. Retrying with max_tokens={strategic_token_limit}.")
        logger.warning("See https://github.com/assafelovic/gpt-researcher/issues/1022")
        try:
            # Retry with same provider but different max_tokens
            provider = GenericLLMProvider.from_provider(
                research_config.STRATEGIC_LLM_PROVIDER,
                model=research_config.STRATEGIC_LLM_MODEL,
                temperature=research_config.TEMPERATURE,
                max_tokens=strategic_token_limit,
                **research_config.llm_kwargs,
            )
            response = await provider.get_chat_response(
                messages=[{"role": "user", "content": llm_queries_prompt}],
                stream=False,
            )
            logger.warning(f"Retrying with max_tokens={strategic_token_limit} successful.")
        except Exception as e:
            logger.warning(f"Retrying with max_tokens={strategic_token_limit} failed.")
            logger.warning(f"Error with strategic LLM: {e.__class__.__name__}: {e}. Falling back to smart LLM.")
            # Fall back to smart LLM
            provider = GenericLLMProvider.from_provider(
                research_config.SMART_LLM_PROVIDER,
                model=research_config.SMART_LLM_MODEL,
                temperature=research_config.TEMPERATURE,
                max_tokens=strategic_token_limit,
                **research_config.llm_kwargs,
            )
            response = await provider.get_chat_response(
                messages=[{"role": "user", "content": llm_queries_prompt}],
                stream=False,
            )
            logger.warning("Retrying with smart LLM successful.")

    if cost_callback:
        from gpt_researcher.utils.costs import estimate_llm_cost
        llm_costs = estimate_llm_cost(llm_queries_prompt, response)
        cost_callback(llm_costs)

    result = json_repair.loads(response)
    if isinstance(result, float):
        raise TypeError("Result is a float somehow")
    if isinstance(result, dict):
        return result.get("queries", [])
    if isinstance(result, str):
        return [result]
    if isinstance(result, int):
        return [str(result)]
    if isinstance(result, list):
        return [item for sublist in result for item in sublist]
    return []
