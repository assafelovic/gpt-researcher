from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from backend.server.logging_config import get_json_handler
from gpt_researcher.actions.query_processing import get_search_results, plan_research_outline
from gpt_researcher.actions.utils import stream_output
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.document.langchain_document import LangChainDocumentLoader
from gpt_researcher.document.online_document import OnlineDocumentLoader
from gpt_researcher.utils.enum import ReportSource


if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher
    from gpt_researcher.retrievers.retriever_abc import RetrieverABC
    from gpt_researcher.utils.logging_config import JSONResearchHandler


from gpt_researcher.utils.logger import get_formatted_logger


logger: logging.Logger = get_formatted_logger()


class ResearchConductor:
    """Manages and coordinates the research process."""

    def __init__(self, researcher: GPTResearcher) -> None:
        self.researcher: GPTResearcher = researcher
        self.logger: logging.Logger = logging.getLogger("research")
        self.json_handler: JSONResearchHandler | None = get_json_handler()

    async def plan_research(
        self,
        query: str,
        query_domains: list[str] | None = None,
    ) -> list[str]:
        self.logger.info(f"Planning research for query: {query}")
        if query_domains:
            self.logger.info(f"Query domains: {query_domains}")

        await stream_output(
            "logs",
            "planning_research",
            f"🌐 Browsing the web to learn more about the task: {query}...",
            self.researcher.websocket,
        )

        search_results: list[dict[str, Any]] = await get_search_results(
            query,
            self.researcher.retrievers[0],
            query_domains,
        )
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
        """Runs the GPT Researcher to conduct research, handling different source types and errors.

        Returns:
            list[str]: A list of research data accumulated during the research.
        """
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
            await stream_output("logs", "agent_generated", self.researcher.agent, self.researcher.websocket)

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
                additional_research = await self._get_context_by_web_search(
                    self.researcher.query,
                    [],
                    self.researcher.query_domains,
                )
                research_data += " ".join(additional_research)

        elif self.researcher.report_source == ReportSource.Web:
            self.logger.info("Using web search")
            research_data = await self._get_context_by_web_search(
                self.researcher.query,
                [],
                self.researcher.query_domains,
            )

        elif self.researcher.report_source == ReportSource.Local:
            self.logger.info("Using local search")
            document_data: list[dict[str, Any]] = await DocumentLoader(self.researcher.cfg.doc_path).load()
            self.logger.info(f"Loaded {len(document_data)} documents")
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)

            research_data = await self._get_context_by_web_search(
                self.researcher.query,
                document_data,
                self.researcher.query_domains,
            )

        elif self.researcher.report_source == ReportSource.Hybrid:
            if self.researcher.document_urls:
                document_data = await OnlineDocumentLoader(self.researcher.document_urls).load()
            else:
                document_data = await DocumentLoader(self.researcher.cfg.DOC_PATH).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)
            docs_context: str = await self._get_context_by_web_search(
                self.researcher.query,
                document_data,
                self.researcher.query_domains,
            )
            web_context: str = await self._get_context_by_web_search(
                self.researcher.query,
                [],
                self.researcher.query_domains,
            )
            research_data = f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"

        elif self.researcher.report_source == ReportSource.Azure:
            from gpt_researcher.document.azure_document_loader import AzureDocumentLoader

            azure_loader = AzureDocumentLoader(
                container_name=os.getenv("AZURE_CONTAINER_NAME"),
                connection_string=os.getenv("AZURE_CONNECTION_STRING"),
            )
            azure_files: list[str] = await azure_loader.load()
            document_data = await DocumentLoader(azure_files).load()  # Reuse existing loader
            research_data = await self._get_context_by_web_search(self.researcher.query, document_data)

        elif self.researcher.report_source == ReportSource.LangChainDocuments:
            langchain_documents_data = await LangChainDocumentLoader(self.researcher.documents).load()
            if self.researcher.vector_store is not None:
                self.researcher.vector_store.load(langchain_documents_data)
            research_data = await self._get_context_by_web_search(
                self.researcher.query,
                langchain_documents_data,
                self.researcher.query_domains,
            )

        elif self.researcher.report_source == ReportSource.LangChainVectorStore:
            research_data = await self._get_context_by_vectorstore(
                self.researcher.query,
                self.researcher.vector_store_filter,
            )

        else:
            raise ValueError(f"Invalid report source: {self.researcher.report_source}")

        # Rank and curate the sources
        self.researcher.context.extend(research_data)
        if self.researcher.cfg.CURATE_SOURCES:
            self.logger.info("Curating and ranking sources...")
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
    ) -> list[str]:
        """Scrapes and compresses the context from the given urls"""
        self.logger.info(f"Getting context from URLs: {urls}")

        new_search_urls: list[str] = await self._get_new_urls(urls)
        self.logger.info(f"New URLs to process: {new_search_urls}")

        scraped_content: list[dict[str, Any]] = await self.researcher.scraper_manager.browse_urls(new_search_urls)
        self.logger.info(f"Scraped content from {len(scraped_content)} URLs. Size: {len(str(scraped_content))}")

        if self.researcher.vector_store is not None:
            self.logger.info("Loading content into vector store")
            self.researcher.vector_store.load(scraped_content)

        context: str = await self.researcher.context_manager.get_similar_content_by_query(
            self.researcher.query,
            scraped_content,
        )
        return context

    # Add logging to other methods similarly...

    async def _get_context_by_vectorstore(
        self,
        query,
        vector_store_filter: dict | None = None,
    ) -> list[str]:
        """Generates the context for the research task by searching the vectorstore

        Returns:
            context: List of context
        """
        self.logger.info(f"Starting vectorstore search for query: {query}")
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
        context: list[str] = await asyncio.gather(
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
        scraped_data: list[str] | None = None,
        query_domains: list[str] | None = None,
    ) -> str:
        """Generates the context for the research task by searching the query and scraping the results

        Args:
            query (str): The query to search for.
            scraped_data (list[str] | None): List of scraped data to use for context.
                Defaults to None.
            query_domains (list[str] | None): List of domains to restrict the search to.

        Returns:
            context: List of context
        """
        self.logger.info(f"Starting web search for query: {query}")

        scraped_data = [] if scraped_data is None else scraped_data
        query_domains = [] if query_domains is None else query_domains

        # Generate Sub-Queries including original query
        sub_queries: list[str] = await self.plan_research(query, query_domains)
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

        try:
            context: list[str] = await asyncio.gather(
                *[
                    self._process_sub_query(
                        sub_query,
                        scraped_data,
                        query_domains,  # Using asyncio.gather to process the sub_queries asynchronously
                    )
                    for sub_query in sub_queries
                ]
            )
            self.logger.info(f"Gathered context from {len(context)} sub-queries")
            # Filter out empty results and join the context
            context = [c for c in context if c and c.strip()]
            if context:
                combined_context = " ".join(context)
                self.logger.info(f"Combined context size: {len(combined_context)}")
                return combined_context
            return ""
        except Exception as e:
            self.logger.exception(f"Error during web search: {e.__class__.__name__}: {e}", exc_info=True)
            return ""

    async def _process_sub_query(
        self,
        sub_query: str,
        scraped_data: list[dict[str, Any]] | None = None,
        query_domains: list[str] | None = None,
    ) -> str:
        """Takes in a sub query and scrapes urls based on it and gathers context."""
        scraped_data = [] if scraped_data is None else scraped_data
        query_domains = [] if query_domains is None else query_domains
        self.logger.info("Processing sub-query: %s", sub_query)
        if self.json_handler is not None:
            self.json_handler.log_event(
                "sub_query",
                {"query": sub_query, "scraped_data_size": len(scraped_data)},
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
                scraped_data = await self._scrape_data_by_urls(sub_query, query_domains)
                self.logger.info(f"Scraped data size: {len(scraped_data)}")
                # Debug the actual content of scraped data
                for idx, data in enumerate(scraped_data):
                    self.logger.info(f"Document {idx} content length: {len(data.get('raw_content', ''))}")
                    self.logger.info(f"Document {idx} url: {data.get('url', 'no url')}")

            content: str = await self.researcher.context_manager.get_similar_content_by_query(
                sub_query,
                scraped_data,
            )
            self.logger.info(f"Content found for sub-query '{sub_query}' was {len(content)} chars")

            if content and content.strip() and self.researcher.verbose:
                await stream_output("logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket)
            elif self.researcher.verbose:
                await stream_output(
                    "logs",
                    "subquery_context_not_found",
                    f"🤷 No content found for '{sub_query}'...",
                    self.researcher.websocket,
                )
        except Exception as e:
            self.logger.exception(f"Error processing sub-query {sub_query}! {e.__class__.__name__}: {e}")
            return ""
        else:
            if content and content.strip():
                if self.json_handler is not None:
                    self.json_handler.log_event("content_found", {"sub_query": sub_query, "content_size": len(content)})
            return content

    async def _process_sub_query_with_vectorstore(
        self,
        sub_query: str,
        sub_filter: dict[str, Any] | None = None,
    ) -> str:
        """Processes a sub-query using a vector store.

        Args:
            sub_query (str): The sub-query to process.
            sub_filter (dict[str, Any] | None): Optional filter to apply to the vector store.

        Returns:
            str: The processed sub-query.
        """
        sub_filter = sub_filter if sub_filter is not None else {}
        if self.researcher.cfg.VERBOSE:
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

        self.logger.debug(f"Content found for sub-query: {len(content) if content else 0} chars")
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
        url_set_input: set[str],
    ) -> list[str]:
        """Gets the new urls from the given url set, avoiding duplicates.

        Args:
            url_set_input (set[str]): The url set to get the new urls from

        Returns:
            list[str]:The new urls from the given url set
        """
        new_urls: list[str] = []
        for url in url_set_input:
            if url in self.researcher.visited_urls:
                continue
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

    async def _search_relevant_source_urls(
        self,
        query: str,
        query_domains: list[str] | None = None,
    ) -> list[str]:
        """Searches for relevant source URLs based on the given query and domains.

        Args:
            query (str): The query to search for.
            query_domains (list[str] | None): List of domains to restrict the search to.
                Defaults to None.

        Returns:
            list[str]: A list of relevant source URLs.
        """
        new_search_urls: set[str] = set()
        query_domains = [] if query_domains is None else query_domains

        # Iterate through all retrievers
        for retriever_class in self.researcher.retrievers:
            if issubclass(retriever_class, BaseRetriever):
                try:
                    retriever_params: dict[str, str] = {"query": query}
                    lang_retriever = retriever_class(**retriever_params)  # type: ignore[arg-type]
                except TypeError as e:
                    self.logger.exception(
                        f"Error instantiating retriever {retriever_class.__name__}! {e.__class__.__name__}: {e}"
                    )
                    continue

                try:
                    search_results_list: list[Document] = await lang_retriever.ainvoke(query)
                    if search_results_list:
                        search_urls: list[str] = [
                            str(
                                webpage.metadata.get(
                                    "source",
                                    webpage.metadata.get("href", "") or "",
                                )
                            ).strip()
                            for webpage in search_results_list
                        ]
                        new_search_urls.update(search_urls)
                except Exception as e:
                    self.logger.exception(
                        f"Error during search with {retriever_class.__name__}! {e.__class__.__name__}: {e}"
                    )
                    continue
            else:
                # Instantiate the retriever with the sub-query
                retriever: RetrieverABC = retriever_class(
                    query,
                    query_domains=query_domains,
                )

                # Perform the search using the current retriever
                search_results: list[dict[str, Any]] = await asyncio.to_thread(
                    retriever.search,
                    max_results=self.researcher.cfg.MAX_SEARCH_RESULTS_PER_QUERY,
                )

                # Collect new URLs from search results
                new_search_urls.update(url.get("href") for url in search_results if url.get("href"))

        # Get unique URLs
        new_search_urls = await self._get_new_urls(new_search_urls)
        random.shuffle(new_search_urls)

        return new_search_urls

    async def _scrape_data_by_urls(
        self,
        sub_query: str,
        query_domains: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Scrapes data from URLs found by searching a sub-query.

        Args:
            sub_query (str): The sub-query to search for.
            query_domains (list[str] | None): Optional list of domains to focus the search on.

        Returns:
            list[dict[str, Any]]: A list of dictionaries containing the scraped data.
        """
        query_domains = [] if query_domains is None else query_domains
        self.logger.info(f"Scraping data for sub-query: {sub_query}")
        new_search_urls: list[str] = await self._search_relevant_source_urls(sub_query, query_domains)

        # Log the research process if verbose mode is on
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "researching",
                "🤔 Researching for relevant information across multiple sources...\n",
                self.researcher.websocket,
            )

        # Scrape the new URLs
        scraped_content: list[dict[str, Any]] = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store is not None:
            self.researcher.vector_store.load(scraped_content)

        return scraped_content
