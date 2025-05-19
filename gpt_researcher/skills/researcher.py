from __future__ import annotations

import asyncio
import logging
import random

from typing import TYPE_CHECKING, Any

from ..actions.query_processing import get_search_results, plan_research_outline
from ..actions.utils import stream_output
from ..document import DocumentLoader, LangChainDocumentLoader, OnlineDocumentLoader
from ..utils.enum import ReportSource
from ..utils.logging_config import get_json_handler

if TYPE_CHECKING:
    from ..agent import GPTResearcher


class ResearchConductor:
    """Manages and coordinates the research process."""

    def __init__(self, researcher: GPTResearcher):
        self.researcher: GPTResearcher = researcher
        self.logger: logging.Logger = logging.getLogger("research")
        self.json_handler: Any | None = get_json_handler()

    async def plan_research(self, query: str) -> list[str]:
        self.logger.info(f"Planning research for query: {query}")

        await stream_output(
            "logs",
            "planning_research",
            f"🌐 Browsing the web to learn more about the task: {query}...",
            self.researcher.websocket,
        )

        search_results: list[dict[str, Any]] = await get_search_results(query, self.researcher.retrievers[0])
        self.logger.info(f"Initial search results obtained: {len(search_results)} results")

        await stream_output(
            "logs",
            "planning_research",
            "🤔 Planning the research strategy and subtasks...",
            self.researcher.websocket,
        )

        outline: list[str] = await plan_research_outline(
            query=query,
            search_results=search_results,
            agent_role_prompt=self.researcher.role,
            cfg=self.researcher.cfg,
            parent_query=self.researcher.parent_query,
            report_type=self.researcher.report_type,
            cost_callback=self.researcher.add_costs,
        )
        self.logger.info(f"Research outline planned: {outline}")
        return outline

    async def conduct_research(self) -> list[str]:
        """Runs the GPT Researcher to conduct research"""
        if self.json_handler is not None:
            self.json_handler.update_content("query", self.researcher.query)

        self.logger.info(f"Starting research for query: {self.researcher.query}")

        # Reset visited_urls and source_urls at the start of each research task
        self.researcher.visited_urls = (
            set()
            if self.researcher.visited_urls is None
            else self.researcher.visited_urls
        )
        research_data: list[str] = []

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "starting_research",
                f"🔍 Starting the research task for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        if self.researcher.verbose:
            await stream_output("logs", "agent_generated", self.researcher.agent, self.researcher.websocket)

        # Research for relevant sources based on source types below
        if self.researcher.source_urls:
            self.logger.info("Using provided source URLs")
            research_data = await self._get_context_by_urls(self.researcher.source_urls)
            if research_data and len(research_data) == 0 and self.researcher.verbose:
                await stream_output(
                    "logs",
                    "answering_from_memory",
                    "🧐 I was unable to find relevant context in the provided sources...",
                    self.researcher.websocket,
                )
            if self.researcher.complement_source_urls:
                self.logger.info("Complementing with web search")
                additional_research: list[str] = await self._get_context_by_web_search(self.researcher.query)
                research_data += " ".join(additional_research)

        elif self.researcher.report_source == ReportSource.Web.value:
            self.logger.info("Using web search")
            research_data = await self._get_context_by_web_search(self.researcher.query)

        elif self.researcher.report_source == ReportSource.Local.value:
            self.logger.info("Using local search")
            document_data: list[str] = await DocumentLoader(self.researcher.cfg.doc_path).load()
            self.logger.info(f"Loaded {len(document_data)} documents")
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)

            research_data = await self._get_context_by_web_search(self.researcher.query, document_data)

        # Hybrid search including both local documents and web sources
        elif self.researcher.report_source == ReportSource.Hybrid.value:
            document_data: list[str] = (
                DocumentLoader(self.researcher.cfg.doc_path)
                if self.researcher.document_urls is None
                else OnlineDocumentLoader(self.researcher.document_urls)
            ).load()
            if self.researcher.vector_store is not None:
                self.researcher.vector_store.load(document_data)
            docs_context: list[str] = await self._get_context_by_web_search(self.researcher.query, document_data)
            web_context: list[str] = await self._get_context_by_web_search(self.researcher.query)
            research_data = f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"
            docs_context: list[str] = await self._get_context_by_web_search(
                self.researcher.query,
                document_data,
                self.researcher.query_domains,
            )
            web_context: list[str] = await self._get_context_by_web_search(
                self.researcher.query,
                [],
                self.researcher.query_domains,
            )
            research_data = self.researcher.prompt_family.join_local_web_documents(docs_context, web_context)

        elif self.researcher.report_source == ReportSource.LangChainDocuments.value:
            langchain_documents_data: list[dict[str, Any]] = await LangChainDocumentLoader(self.researcher.documents).load()
            if self.researcher.vector_store is not None:
                self.researcher.vector_store.load(langchain_documents_data)
            research_data = await self._get_context_by_web_search(
                self.researcher.query,
                langchain_documents_data,
            )

        elif self.researcher.report_source == ReportSource.LangChainVectorStore.value:
            research_data = await self._get_context_by_vectorstore(
                self.researcher.query,
                self.researcher.vector_store_filter,
            )

        # Rank and curate the sources
        self.researcher.context = research_data
        if self.researcher.cfg.curate_sources:  # pyright: ignore[reportAttributeAccessIssue]
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

    async def _get_context_by_urls(self, urls: list[str]) -> list[str]:
        """Scrapes and compresses the context from the given urls"""
        self.logger.info(f"Getting context from URLs: {urls}")

        new_search_urls: list[str] = await self._get_new_urls(urls)
        self.logger.info(f"New URLs to process: {new_search_urls}")

        scraped_content: list[str] = await self.researcher.scraper_manager.browse_urls(new_search_urls)
        self.logger.info(f"Scraped content from {len(scraped_content)} URLs")

        if self.researcher.vector_store:
            self.logger.info("Loading content into vector store")
            self.researcher.vector_store.load(scraped_content)

        context: list[str] = await self.researcher.context_manager.get_similar_content_by_query(
            self.researcher.query,
            scraped_content,
        )
        self.logger.info(f"Generated context length: {len(context)}")
        return context

    # Add logging to other methods similarly...

    async def _get_context_by_vectorstore(
        self,
        query: str,
        filter: dict[str, Any] | None = None,
    ) -> list[str]:
        """Generates the context for the research task by searching the vectorstore

        Args:
            query (str): The query to search the vectorstore for
            filter (dict[str, Any] | None): The filter to apply to the vectorstore

        Returns:
            context: List of context
        """
        context: list[str] = []
        # Generate Sub-Queries including original query
        sub_queries: list[str] = await self.plan_research(query)
        # If this is not part of a sub researcher, add original query to research for better results
        if self.researcher.report_type != "subtopic_report":
            sub_queries.append(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️  I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                True,
                sub_queries,
            )

        # Using asyncio.gather to process the sub_queries asynchronously
        context = await asyncio.gather(
            *[
                self._process_sub_query_with_vectorstore(sub_query, filter)
                for sub_query in sub_queries
            ]
        )
        return context

    async def _get_context_by_web_search(
        self,
        query: str,
        scraped_data: list[str] | None = None,
        query_domains: list[str] | None = None,
    ) -> list[str]:
        """Generates the context for the research task by searching the query and scraping the results.
        Args:
            query (str): The query to search the web for
            scraped_data (list[str] | None): The scraped data to use for the research
            query_domains (list[str] | None): The domains to search the web for

        Returns:
            context: List of context
        """
        self.logger.info(f"Starting web search for query: {query}")

        # Generate Sub-Queries including original query
        sub_queries: list[str] = await self.plan_research(query)
        self.logger.info(f"Generated sub-queries: {sub_queries}")

        # If this is not part of a sub researcher, add original query to research for better results
        if self.researcher.report_type != "subtopic_report":
            sub_queries.append(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️ I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                True,
                sub_queries,
            )

        # Using asyncio.gather to process the sub_queries asynchronously
        try:
            context: list[str] = await asyncio.gather(*[self._process_sub_query(sub_query, scraped_data or []) for sub_query in sub_queries])
            self.logger.info(f"Gathered context from {len(context)} sub-queries")
            # Filter out empty results and join the context
            context = [c for c in context if c]
            if context:
                combined_context: str = " ".join(context)
                self.logger.info(f"Combined context size: {len(combined_context)}")
                return combined_context
            return []
        except Exception as e:
            self.logger.error(f"Error during web search: {e.__class__.__name__}: {e}", exc_info=True)
            return []

    async def _process_sub_query(
        self,
        sub_query: str,
        scraped_data: list[str] | None = None,
    ) -> str:
        """Takes in a sub query and scrapes urls based on it and gathers context."""
        if self.json_handler is not None:
            self.json_handler.log_event("sub_query", {"query": sub_query, "scraped_data_size": len(scraped_data)})

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

            content = await self.researcher.context_manager.get_similar_content_by_query(sub_query, scraped_data)
            self.logger.info(f"Content found for sub-query: {len(str(content)) if content else 0} chars")

            if content and self.researcher.verbose:
                await stream_output("logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket)
            elif self.researcher.verbose:
                await stream_output(
                    "logs",
                    "subquery_context_not_found",
                    f"🤷 No content found for '{sub_query}'...",
                    self.researcher.websocket,
                )
            if content:
                if self.json_handler:
                    self.json_handler.log_event("content_found", {"sub_query": sub_query, "content_size": len(content)})
            return content
        except Exception as e:
            self.logger.error(f"Error processing sub-query {sub_query}: {e}", exc_info=True)
            return ""

    async def _process_sub_query_with_vectorstore(
        self,
        sub_query: str,
        filter: dict[str, Any] | None = None,
    ) -> str:
        """Takes in a sub query and gathers context from the user provided vector store

        Args:
            sub_query (str): The sub-query generated from the original query
            filter (dict[str, Any] | None): The filter to apply to the vector store

        Returns:
            str: The context gathered from search
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_with_vectorstore_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.researcher.websocket,
            )

        content: str = await self.researcher.context_manager.get_similar_content_by_query_with_vectorstore(
            sub_query,
            filter,
        )

        if content and self.researcher.verbose:
            await stream_output("logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket)
        elif self.researcher.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 No content found for '{sub_query}'...",
                self.researcher.websocket,
            )
        return content

    async def _get_new_urls(
        self,
        url_set_input: set[str] | None = None,
    ) -> list[str]:
        """Gets the new urls from the given url set.
        Args:
            url_set_input (set[str] | None): The url set to get the new urls from

        Returns:
            list[str]: The new urls from the given url set
        """

        new_urls: list[str] = []
        for url in url_set_input or []:
            if url not in self.researcher.visited_urls:
                self.researcher.visited_urls.add(url)
                new_urls.append(url)
                if self.researcher.verbose:
                    await stream_output(
                        "logs",
                        "added_source_url",
                        f"✅ Added source url to research: {url}\n",
                        self.researcher.websocket,
                        True,
                        url,
                    )

        return new_urls

    async def _search_relevant_source_urls(self, query: str) -> list[str]:
        """Searches the relevant source urls for the given query.
        Args:
            query (str): The query to search the source urls for

        Returns:
            list[str]: The relevant source urls for the given query
        """
        new_search_urls: list[str] = []

        # Iterate through all retrievers
        for retriever_class in self.researcher.retrievers:
            # Instantiate the retriever with the sub-query
            retriever: Any = retriever_class(query)

            # Perform the search using the current retriever
            search_results: list[dict[str, Any]] = await asyncio.to_thread(
                retriever.search,
                max_results=self.researcher.cfg.max_search_results_per_query,  # pyright: ignore[reportAttributeAccessIssue]
            )

            # Collect new URLs from search results
            search_urls: list[str] = [url.get("href") for url in search_results]
            new_search_urls.extend(search_urls)

        # Get unique URLs
        new_search_urls: list[str] = await self._get_new_urls(new_search_urls)
        random.shuffle(new_search_urls)

        return new_search_urls

    async def _scrape_data_by_urls(self, sub_query: str) -> list[str]:
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
        scraped_content: list[str] = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store:
            self.researcher.vector_store.load(scraped_content)

        return scraped_content
