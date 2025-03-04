from __future__ import annotations

import asyncio
import logging
import os
import random

from typing import TYPE_CHECKING, Any, Callable, Sequence

import json_repair

from backend.server.logging_config import JSONResearchHandler, get_json_handler
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from litellm.utils import get_max_tokens

from gpt_researcher.actions.query_processing import plan_research_outline
from gpt_researcher.actions.utils import stream_output
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.document.langchain_document import LangChainDocumentLoader
from gpt_researcher.document.online_document import OnlineDocumentLoader
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import generate_search_queries_prompt
from gpt_researcher.utils.enum import ReportSource, ReportType

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher
    from gpt_researcher.config import Config
    from gpt_researcher.utils.logging_config import JSONResearchHandler


logger: logging.Logger = logging.getLogger(__name__)


class ResearchConductor:
    """Manages and coordinates the research process."""

    def __init__(
        self,
        researcher: GPTResearcher,
    ):
        self.researcher: GPTResearcher = researcher
        self.logger: logging.Logger = logging.getLogger("research")
        # Prefer get_json_handler if available, otherwise fallback to attribute
        self.json_handler: JSONResearchHandler | None = getattr(self.logger, "json_handler", get_json_handler())
        self.llm_provider: GenericLLMProvider | None = None

    def _get_llm(
        self,
        model: str,
        provider: str,
        temperature: float,
        **llm_kwargs: Any,
    ) -> GenericLLMProvider:
        """Get or create an LLM provider instance.

        Args:
        ----
            model (str): The model to use
            provider (str): The LLM provider to use
            temperature (float): The temperature to use for generation
            **llm_kwargs: Additional keyword arguments to pass to the LLM provider

        Returns:
        -------
            (GenericLLMProvider): The LLM provider instance
        """
        if self.llm_provider is None:
            self.llm_provider = GenericLLMProvider(
                provider,
                model=model,
                temperature=temperature,
                fallback_models=self.researcher.cfg.FALLBACK_MODELS,
                **llm_kwargs,
            )
        return self.llm_provider

    async def plan_research(
        self,
        query: str,
        query_domains: list[str] | None = None,
    ) -> list[str]:
        """Plans the research by generating sub-queries or an outline.

        Args:
        ----
            query (str): The main research query.
            query_domains (list[str] | None): Optional list of domains to focus the search on.

        Returns:
        -------
            (list[str]): A list of sub-queries and/or an outline for the research.
        """
        self.logger.info(f"Planning research for query: {query}")
        if query_domains:
            self.logger.info(f"Query domains: {query_domains}")

        await stream_output(
            "logs",
            "planning_research",
            f"🌐 Browsing the web to learn more about the task: {query}...",
            self.researcher.websocket,
        )
        search_results: list[dict[str, Any]] = []
        for retriever_entry in self.researcher.retrievers:
            try:
                await get_search_results_new(
                    query,
                    retriever_entry,
                    query_domains,
                )
                break
            except Exception as e:
                self.logger.exception(f"Error with retriever {retriever_entry.__name__}! {e.__class__.__name__}: {e}")
        self.logger.info(f"Initial search results obtained: {len(search_results)} results")

        await stream_output(
            "logs",
            "planning_research",
            "🤔 Planning the research strategy and subtasks...",
            self.researcher.websocket,
        )

        # Use plan_research_outline or generate_sub_queries based on configuration
        if self.researcher.cfg.RESEARCH_PLANNER == "outline":
            outline: list[str] = await plan_research_outline(
                query=query,
                search_results=search_results,
                agent_role_prompt=self.researcher.agent_role,
                cfg=self.researcher.cfg,
                parent_query=self.researcher.parent_query,
                report_type=self.researcher.report_type,
                cost_callback=self.researcher.add_costs,
            )
        else:  # Default to sub-queries
            outline = await generate_sub_queries(
                query=query,
                context=search_results,
                cfg=self.researcher.cfg,
                parent_query=self.researcher.parent_query,
                report_type=self.researcher.report_type,
                cost_callback=self.researcher.add_costs,
            )
        self.logger.info(f"Research outline/plan: {outline}")
        return outline

    async def conduct_research(self) -> list[str]:
        """Runs the GPT Researcher to conduct research, handling different source types and errors.

        Returns:
        -------
            (list[str]): A list of research data accumulated during the research.
        """
        if self.json_handler is not None:
            self.json_handler.update_content("query", self.researcher.query)

        self.logger.info(f"Starting research for query: {self.researcher.query}")

        # Reset visited_urls at the start of each research task
        self.researcher.visited_urls.clear()

        if self.researcher.cfg.VERBOSE:
            await self._stream_research_start()

        try:
            research_data: list[str] = await self._gather_research_data()
        except Exception as e:
            self.logger.exception(f"Failed to gather research data: {e.__class__.__name__}: {e}")
            return []  # Return empty list on failure

        if self.researcher.cfg.CURATE_SOURCES:
            try:
                self.logger.info("Curating sources")
                self.researcher.context = await self.researcher.source_curator.curate_sources(research_data)
            except Exception as e:
                self.logger.warning(f"Source curation failed, using original sources: {e.__class__.__name__}: {e}", exc_info=True)
                self.researcher.context.extend(research_data)
        else:
            self.researcher.context.extend(research_data)


        if self.researcher.cfg.VERBOSE:
            await self._stream_research_finalization()

        self.logger.info(f"RESEARCH COMPLETED! Total Context Length: {len(str(self.researcher.context))}")
        return self.researcher.context

    async def _stream_research_start(self) -> None:
        """Streams the initial research start messages."""
        await stream_output(
            "logs",
            "starting_research",
            f"🔍 Starting the research task for '{self.researcher.query}'...",
            self.researcher.websocket,
        )
        await stream_output(
            "logs",
            "agent_generated",
            self.researcher.agent or "🤖 I am an AI Researcher, here to help you with your queries...",
            self.researcher.websocket,
        )

    async def _gather_research_data(self) -> list[str]:
        """Gathers research data based on the configured source type."""
        research_data: list[str] = []

        if self.researcher.source_urls:
            research_data = await self._handle_provided_urls()
        elif self.researcher.cfg.REPORT_SOURCE == ReportSource.Web:
            research_data = [await self._get_context_by_web_search(
                self.researcher.query, query_domains=self.researcher.query_domains
            )]
        elif self.researcher.cfg.REPORT_SOURCE == ReportSource.Local:
            research_data = await self._handle_local_documents()
        elif self.researcher.cfg.REPORT_SOURCE == ReportSource.Hybrid:
            research_data = await self._handle_hybrid_search()
        elif self.researcher.cfg.REPORT_SOURCE == ReportSource.LangChainDocuments:
            research_data = await self._handle_langchain_documents()
        elif self.researcher.cfg.REPORT_SOURCE == ReportSource.LangChainVectorStore:
            research_data = await self._get_context_by_vectorstore(
                self.researcher.query, self.researcher.vector_store_filter
            )
        elif self.researcher.cfg.REPORT_SOURCE == ReportSource.Azure:
            research_data = await self._handle_azure_documents()
        else:
            raise ValueError(f"Invalid report source: {self.researcher.cfg.REPORT_SOURCE}")

        return research_data if isinstance(research_data, list) else [research_data]

    async def _handle_provided_urls(self) -> list[str]:
        """Handles research when source URLs are provided."""
        self.logger.info("Using provided source URLs")
        research_data: list[str] = []
        try:
            context: str = await self._get_context_by_urls(self.researcher.source_urls)
            research_data.append(context)
        except Exception as e:
            self.logger.exception(f"Error getting context from provided URLs: {e.__class__.__name__}: {e}")
            # Optionally, allow fallback to web search or other strategies
            return []

        if not research_data[0] and self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "answering_from_memory",
                "🧐 I was unable to find relevant context in the provided sources...",
                self.researcher.websocket,
            )
        if self.researcher.complement_source_urls:
            self.logger.info("Complementing with web search")
            try:
                additional_research: list[str] = [
                    await self._get_context_by_web_search(
                        self.researcher.query,
                        query_domains=self.researcher.query_domains,
                    )
                ]
                research_data.extend(additional_research)
            except Exception as e:
                self.logger.exception(f"Error during complementary web search: {e.__class__.__name__}: {e}")
                # Decide whether to continue without the additional research or return an empty list

        return research_data

    async def _handle_local_documents(self) -> list[str]:
        """Handles research using local documents."""
        try:
            document_data: list[dict[str, Any]] = await DocumentLoader(self.researcher.cfg.DOC_PATH).load()
            if self.researcher.vector_store is not None:
                self.researcher.vector_store.load(document_data)
            context: str = await self._get_context_by_web_search(
                self.researcher.query,
                document_data,
                query_domains=self.researcher.query_domains,
            )
            return [context]
        except Exception as e:
            self.logger.exception(f"Error handling local documents: {e.__class__.__name__}: {e}")
            return []

    async def _handle_hybrid_search(self) -> list[str]:
        """Handles hybrid search including both local documents and web sources."""
        try:
            document_data: list[dict[str, Any]] = (
                await OnlineDocumentLoader(self.researcher.document_urls).load()
                if self.researcher.document_urls
                else await DocumentLoader(self.researcher.cfg.DOC_PATH).load()
            )
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)

            docs_context: str = await self._get_context_by_web_search(
                self.researcher.query,
                document_data,
                query_domains=self.researcher.query_domains,
            )
            web_context: str = await self._get_context_by_web_search(
                self.researcher.query,
                query_domains=self.researcher.query_domains,
            )
            return [f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"]

        except Exception as e:
            self.logger.exception(f"Error during Hybrid search: {e.__class__.__name__}: {e}")
            return []  # Return an empty list or handle partial results

    async def _handle_langchain_documents(self) -> list[str]:
        """Handles research using LangChain documents."""
        try:
            self.logger.info("Using LangChain documents")
            lang_docs: list[Document] = [Document(**doc) for doc in self.researcher.documents]
            langchain_documents_data: list[dict[str, Any]] = await LangChainDocumentLoader(lang_docs).load()
            if self.researcher.vector_store is not None:
                self.researcher.vector_store.load(langchain_documents_data)
            context: str = await self._get_context_by_web_search(
                self.researcher.query,
                langchain_documents_data,
                query_domains=self.researcher.query_domains,
            )
            return [context]
        except Exception as e:
            self.logger.exception(f"Error handling LangChain documents: {e.__class__.__name__}: {e}")
            return []

    async def _handle_azure_documents(self) -> list[str]:
        """Handles research using Azure Document Loader."""
        try:
            from gpt_researcher.document.azure_document_loader import AzureDocumentLoader

            self.logger.info("Using Azure Document Loader")
            azure_loader = AzureDocumentLoader(
                container_name=os.getenv("AZURE_CONTAINER_NAME", ""),
                connection_string=os.getenv("AZURE_CONNECTION_STRING", ""),
            )
            azure_files: list[Any] = await azure_loader.load()
            document_data: list[dict[str, Any]] = await DocumentLoader(azure_files).load()  # Reuse existing loader
            context: str = await self._get_context_by_web_search(self.researcher.query, document_data)
            return [context]
        except ImportError as e:
            self.logger.exception(f"Azure Document Loader dependency not found: {e.__class__.__name__}: {e}")
            return []
        except Exception as e:
            self.logger.exception(f"Error handling Azure documents: {e.__class__.__name__}: {e}")
            return []

    async def _stream_research_finalization(self) -> None:
        """Streams the final research step messages."""
        await stream_output(
            "logs",
            "research_step_finalized",
            f"Finalized research step.\n💸 Total Research Costs: ${self.researcher.get_costs()}",
            self.researcher.websocket,
        )
        if self.json_handler is not None:
            self.json_handler.update_content("costs", self.researcher.get_costs())
            self.json_handler.update_content("context", self.researcher.context)

    async def _get_context_by_urls(
        self,
        urls: list[str],
    ) -> str:
        """Scrapes and compresses the context from the given urls.

        Args:
        ----
            urls (list[str]): List of URLs to scrape.

        Returns:
        -------
            context (str): Context string.
        """
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

    async def _get_context_by_vectorstore(
        self,
        query: str,
        vector_store_filter: dict[str, Any] | None = None,
    ) -> list[str]:
        """Generates the context for the research task by searching the vectorstore.

        Args:
        ----
            query (str): The query to search for.
            filter (dict[str, Any] | None): The filter to apply to the vectorstore.

        Returns:
        -------
            context (list[str]): List of context.
        """
        self.logger.info(f"Starting vectorstore search for query: {query}")
        # Generate Sub-Queries including original query
        sub_queries: list[str] = await self.plan_research(query)
        # If this is not part of a sub researcher, add original query to research for better results
        if self.researcher.report_type != ReportType.SubtopicReport:
            sub_queries.append(query)

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️  I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                output_log=True,
                metadata={"queries": sub_queries},
            )

        # Using asyncio.gather to process the sub_queries asynchronously
        context_list: list[str] = await asyncio.gather(
            *[
                self._process_sub_query_with_vectorstore(
                    sub_query,
                    vector_store_filter,
                )
                for sub_query in sub_queries
            ]
        )
        self.logger.info(f"Gathered context from {len(context_list)} sub-queries using vectorstore")
        return context_list

    async def _get_context_by_web_search(
        self,
        query: str,
        scraped_data: list[dict[str, Any]] | None = None,
        query_domains: list[str] | None = None,
    ) -> str:
        """Generates the context for the research task by searching the query and scraping the results.

        Args:
        ----
            query (str): The query to search for.
            scraped_data (list[dict[str, Any]]): List of scraped data (can be from documents).
            query_domains (list[str] | None): Optional list of domains to focus the search on.

        Returns:
        -------
            context (str): Context string.
        """
        scraped_data = scraped_data if scraped_data is not None else []
        self.logger.info(f"Starting web search for query: {query}")

        # Generate Sub-Queries including original query
        sub_queries: list[str] = await self.plan_research(query, query_domains)
        self.logger.info(f"Generated sub-queries: {sub_queries}")

        # If this is not part of a sub researcher, add original query to research for better results
        if self.researcher.report_type != ReportType.SubtopicReport:
            sub_queries.append(query)

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️ I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                output_log=True,
                metadata={"queries": sub_queries},
            )

        # Using asyncio.gather to process the sub_queries asynchronously
        try:
            context: list[str] = await asyncio.gather(
                *[
                    self._process_sub_query(
                        sub_query,
                        scraped_data,
                        query_domains,
                    )
                    for sub_query in sub_queries
                ]
            )
            self.logger.info(f"Gathered context from {len(context)} sub-queries")
            # Filter out empty results and join the context
            context_str: str = " ".join(c for c in context if c.strip())
            self.logger.info(f"Combined context size: {len(context_str)}")
            return context_str
        except Exception as e:
            self.logger.exception(f"Error during web search: {e.__class__.__name__}: {e}")
            return ""

    async def _process_sub_query(
        self,
        sub_query: str,
        scraped_data: list[dict[str, Any]] | None = None,
        query_domains: list[str] | None = None,
    ) -> str:
        """Takes in a sub query and scrapes urls based on it and gathers context.

        Args:
        ----
            sub_query (str): The sub-query to process.
            scraped_data (list[dict[str, Any]] | None): Optional list of scraped data.
            query_domains (list[str] | None): Optional list of domains to focus the search on.

        Returns:
        -------
            (str): The processed sub-query.
        """
        scraped_data = scraped_data if scraped_data is not None else []
        if self.json_handler is not None:
            self.json_handler.log_event(
                "sub_query",
                {
                    "query": sub_query,
                    "scraped_data_size": len(scraped_data),
                },
            )

        if self.researcher.cfg.VERBOSE:
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

            content: str = await self.researcher.context_manager.get_similar_content_by_query(
                sub_query,
                scraped_data,
            )
            self.logger.info(f"Content found for sub-query was {len(content)} chars")

            if content and content.strip():
                await stream_output(
                    "logs",
                    "subquery_context_window",
                    f"📃 {content}",
                    self.researcher.websocket,
                )
                if self.researcher.cfg.VERBOSE and self.json_handler is not None:
                    self.json_handler.log_event(
                        "content_found",
                        {
                            "sub_query": sub_query,
                            "content_size": len(content),
                        },
                    )
            elif self.researcher.cfg.VERBOSE:
                await stream_output(
                    "logs",
                    "subquery_context_not_found",
                    f"🤷 No content found for '{sub_query}'...",
                    self.researcher.websocket,
                )
            return content
        except Exception as e:
            self.logger.exception(f"Error processing sub-query {sub_query}! {e.__class__.__name__}: {e}")
            return ""

    async def _process_sub_query_with_vectorstore(
        self,
        sub_query: str,
        sub_filter: dict[str, Any] | None = None,
    ) -> str:
        """Processes a sub-query using a vector store.

        Args:
        ----
            sub_query (str): The sub-query to process.
            sub_filter (dict[str, Any] | None): Optional filter to apply to the vector store.

        Returns:
        -------
            (str): The processed sub-query.
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
        if not self.researcher.cfg.VERBOSE:
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
        """Gets the new urls from the given url set, avoiding duplicates."""

        new_urls: list[str] = []
        for url in url_set_input:
            if url in self.researcher.visited_urls:
                continue
            self.researcher.visited_urls.add(url)
            new_urls.append(url)
            if not self.researcher.cfg.VERBOSE:
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
        query_domains: list[str] | None = None,
    ) -> list[str]:
        """Searches for relevant source URLs using available retrievers."""
        new_search_urls: set[str] = set()

        # Iterate through all retrievers
        for retriever_class in self.researcher.retrievers:
            if issubclass(retriever_class, BaseRetriever):
                # Instantiate the retriever
                try:
                    # For Langchain retrievers, we need to check if they accept our parameters
                    # Some may not accept query_domains or config
                    retriever_params: dict[str, str] = {"query": query}
                    retriever: BaseRetriever = retriever_class(**retriever_params)  # type: ignore[arg-type]
                except TypeError as e:
                    self.logger.exception(f"Error instantiating retriever {retriever_class.__name__}! {e.__class__.__name__}: {e}")
                    continue

                # Perform the search and collect URLs
                try:
                    search_results_list: Sequence[Document | dict[str, Any]] | None = await retriever.aget_relevant_documents(query)
                    if search_results_list:
                        search_urls: list[str] = [
                            str(
                                webpage.metadata.get(
                                    "source",
                                    webpage.metadata.get("href", ""),
                                ) if isinstance(webpage, Document) else webpage.get("href", "")
                            ).strip()
                            for webpage in search_results_list
                        ]
                        new_search_urls.update(search_urls)

                except Exception as e:
                    self.logger.exception(f"Error during search with {retriever_class.__name__}! {e.__class__.__name__}: {e}")
                    continue
            else:
                retriever = retriever_class(
                    query, 
                    query_domains=query_domains,
                    config=self.researcher.cfg
                )  # type: ignore[attr-defined]

                search_results_list = await asyncio.to_thread(
                    retriever.search,
                    max_results=self.researcher.cfg.MAX_SEARCH_RESULTS_PER_QUERY,
                )

                if search_results_list:
                    for url in search_results_list:
                        href = str(url.get("href", "") or "").strip() if isinstance(url, dict) else str(url).strip()
                        if href:
                            new_search_urls.add(href)

        # Get unique and new URLs
        new_search_urls_list: list[str] = await self._get_new_urls(new_search_urls)
        random.shuffle(new_search_urls_list)
        return new_search_urls_list

    async def _scrape_data_by_urls(
        self,
        sub_query: str,
        query_domains: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Scrapes data from URLs found by searching a sub-query.

        Args:
        ----
            sub_query (str): The sub-query to search for.
            query_domains (list[str] | None): Optional list of domains to focus the search on.

        Returns:
        -------
            (list[dict[str, Any]]): A list of dictionaries containing the scraped data.
        """
        new_search_urls: list[str] = await self._search_relevant_source_urls(sub_query, query_domains)

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "researching",
                "🤔 Researching for relevant information across multiple sources...\n",
                self.researcher.websocket,
            )

        scraped_content: tuple[list[dict[str, Any]], list[dict[str, Any]]] = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store is not None:
            self.researcher.vector_store.load(scraped_content[0])

        return scraped_content[0]


async def get_search_results_new(
    query: str,
    retriever: type[BaseRetriever],
    query_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Get web search results for a given query using a Langchain retriever.

    Args:
    ----
        query (str): The query to search for.
        retriever (type[BaseRetriever]): The retriever to use.
        query_domains (list[str] | None): Optional list of domains to focus the search on.

    Returns:
    -------
        (list[dict[str, Any]]): A list of dictionaries containing the search results.
    """
    try:
        retriever_instance: BaseRetriever = retriever(
            query=query,  # type: ignore[arg-type]
            query_domains=query_domains,  # type: ignore[arg-type]
        )
        documents: list[Document] = await retriever_instance.aget_relevant_documents(query)
        return [
            {
                "href": doc.metadata.get("source", ""),
                "title": doc.metadata.get("title", ""),
                "raw_content": doc.page_content,
            }
            for doc in documents
        ]
    except Exception as e:
        logger.exception(f"Error getting search results with retriever {retriever.__name__}! {e.__class__.__name__}: {e}")
        return []  # Return an empty list on error


async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: ReportType,
    context: list[dict[str, Any]],
    cfg: Config,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str]:
    """Generate sub-queries using the specified LLM model.

    Args:
    ----
        query (str): The main research query.
        parent_query (str): The parent query.
        report_type (ReportType): The type of report to generate.
        context (list[dict[str, Any]]): The context to use for the research.
        cfg (Config): The configuration to use for the research.

    Returns:
    -------
        (list[str]): A list of sub-queries.
    """
    llm_queries_prompt: str = generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=cfg.MAX_ITERATIONS or 1,
        context=context,
    )

    strategic_token_limit: int | None = get_max_tokens(cfg.STRATEGIC_LLM_MODEL)
    try:
        provider: GenericLLMProvider = GenericLLMProvider(
            cfg.STRATEGIC_LLM_PROVIDER,
            model=cfg.STRATEGIC_LLM_MODEL,
            temperature=cfg.TEMPERATURE,
            max_tokens=strategic_token_limit,
            fallback_models=cfg.FALLBACK_MODELS,
            **cfg.llm_kwargs,
        )
        response: str = await provider.get_chat_response(
            messages=[{"role": "user", "content": llm_queries_prompt}],
            stream=False,
        )
    except Exception as e:
        logger.warning(f"Error with strategic LLM ({cfg.STRATEGIC_LLM_MODEL}): {e.__class__.__name__}: {e}. Retrying with adjusted max_tokens.", exc_info=True)
        logger.warning("See https://github.com/assafelovic/gpt-researcher/issues/1022")
        try:
            # Retry with the *same* provider, but adjusted max_tokens
            provider = GenericLLMProvider(
                cfg.STRATEGIC_LLM_PROVIDER,
                model=cfg.STRATEGIC_LLM_MODEL,
                temperature=cfg.TEMPERATURE,
                fallback_models=cfg.FALLBACK_MODELS,
                max_tokens=strategic_token_limit,  # Keep original limit
                **cfg.llm_kwargs,
            )
            response = await provider.get_chat_response(messages=[{"role": "user", "content": llm_queries_prompt}], stream=False)
            logger.warning("Retry with adjusted max_tokens successful.")

        except Exception as e2:
            logger.warning(f"Retry with adjusted max_tokens failed: {e2.__class__.__name__}: {e2}. Falling back to smart LLM.", exc_info=True)
            # Fall back to smart LLM
            try:
                provider = GenericLLMProvider(
                    cfg.SMART_LLM_PROVIDER,
                    model=cfg.SMART_LLM_MODEL,
                    temperature=cfg.TEMPERATURE,
                    fallback_models=cfg.FALLBACK_MODELS,
                    max_tokens=strategic_token_limit,
                    **cfg.llm_kwargs,
                )
                response = await provider.get_chat_response(messages=[{"role": "user", "content": llm_queries_prompt}], stream=False)
                logger.warning("Fallback to smart LLM successful.")
            except Exception as e3:
                logger.exception(f"Fallback to smart LLM also failed: {e3.__class__.__name__}: {e3}. Returning empty list.")
                return []

    if cost_callback:
        from gpt_researcher.utils.costs import estimate_llm_cost

        cost_callback(estimate_llm_cost(llm_queries_prompt, response))

    try:
        result: dict[str, Any] | list[Any] | str | float | int | bool | None | tuple[dict[str, Any] | list[Any] | str | float | int | bool | None, list[dict[str, str]]] = (
            json_repair.loads(response)
        )
        # Validate the parsed JSON structure
        if result is None:
            logger.warning(f"JSON response parsed as None for query: {query}")
            return []
    except (TypeError, ValueError) as e:
        logger.exception(f"Failed to parse JSON response for query '{query}': {e.__class__.__name__}: {e.__class__.__name__}: {e}")
        logger.debug(f"Raw response that failed parsing: {response[:500]}...")
        return []

    if isinstance(result, float):
        logger.exception(f"Unexpected float result for query '{query}': {result}")
        return []
    if isinstance(result, dict):
        queries = result.get("queries", [])
        logger.debug(f"Extracted {len(queries)} queries from dict result for '{query}'")
        return queries
    if isinstance(result, (str, int)):
        logger.debug(f"Converting single result to list for query '{query}': {result}")
        return [str(result)]  # Convert to string and wrap in a list
    if isinstance(result, list):
        flattened = [
            item
            for sublist in result  # Flatten list of lists
            for item in (sublist if isinstance(sublist, list) else [sublist])
        ]
        logger.debug(f"Flattened {len(result)} list items to {len(flattened)} items for query '{query}'")
        return flattened
    logger.exception(f"Unexpected result type for query '{query}': `{result.__class__.__name__}`. Result: `{str(result)[:200]}...`")
    return []
