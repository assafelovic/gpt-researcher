import asyncio
import random
import json
from typing import Dict, Optional

from ..actions.utils import stream_output
from ..actions.query_processing import get_sub_queries
from ..document import DocumentLoader, LangChainDocumentLoader
from ..utils.enum import ReportSource, ReportType, Tone


class ResearchConductor:
    """Manages and coordinates the research process."""

    def __init__(self, researcher):
        self.researcher = researcher

    async def conduct_research(self):
        """
        Runs the GPT Researcher to conduct research
        """
        # Reset visited_urls and source_urls at the start of each research task
        self.researcher.visited_urls.clear()
        # Due to deprecation of report_type in favor of report_source,
        # we need to clear source_urls if report_source is not static
        if self.researcher.report_source != "static" and self.researcher.report_type != "sources":
            self.researcher.source_urls = []

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "starting_research",
                f"🔎 Starting the research task for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        if self.researcher.verbose:
            await stream_output("logs", "agent_generated", self.researcher.agent, self.researcher.websocket)

        # If specified, the researcher will use the given urls as the context for the research.
        if self.researcher.source_urls:
            self.researcher.context = await self.__get_context_by_urls(self.researcher.source_urls)

        elif self.researcher.report_source == ReportSource.Local.value:
            document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)

            self.researcher.context = await self.__get_context_by_search(self.researcher.query, document_data)

        # Hybrid search including both local documents and web sources
        elif self.researcher.report_source == ReportSource.Hybrid.value:
            document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)
            docs_context = await self.__get_context_by_search(self.researcher.query, document_data)
            web_context = await self.__get_context_by_search(self.researcher.query)
            self.researcher.context = f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"

        elif self.researcher.report_source == ReportSource.LangChainDocuments.value:
            langchain_documents_data = await LangChainDocumentLoader(
                self.researcher.documents
            ).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(langchain_documents_data)
            self.researcher.context = await self.__get_context_by_search(
                self.researcher.query, langchain_documents_data
            )

        elif self.researcher.report_source == ReportSource.LangChainVectorStore.value:
            self.researcher.context = await self.__get_context_by_vectorstore(self.researcher.query, self.researcher.vector_store_filter)
        # Default web based research
        else:
            self.researcher.context = await self.__get_context_by_search(self.researcher.query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_step_finalized",
                f"Finalized research step.\n💸 Total Research Costs: ${self.researcher.get_costs()}",
                self.researcher.websocket,
            )

        return self.researcher.context

    async def __get_context_by_urls(self, urls):
        """
        Scrapes and compresses the context from the given urls
        """
        new_search_urls = await self.__get_new_urls(urls)
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "source_urls",
                f"🗂️ I will conduct my research based on the following urls: {new_search_urls}...",
                self.researcher.websocket,
            )

        scraped_content = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store:
            self.researcher.vector_store.load(scraped_content)

        return await self.researcher.context_manager.get_similar_content_by_query(self.researcher.query, scraped_content)

    async def __get_context_by_vectorstore(self, query, filter: Optional[dict] = None):
        """
        Generates the context for the research task by searching the vectorstore
        Returns:
            context: List of context
        """
        context = []
        # Generate Sub-Queries including original query
        sub_queries = await self.get_sub_queries(query)
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
                self.__process_sub_query_with_vectorstore(sub_query, filter)
                for sub_query in sub_queries
            ]
        )
        return context

    async def __get_context_by_search(self, query, scraped_data: list = []):
        """
        Generates the context for the research task by searching the query and scraping the results
        Returns:
            context: List of context
        """
        context = []
        # Generate Sub-Queries including original query
        sub_queries = await self.get_sub_queries(query)
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
        context = await asyncio.gather(
            *[
                self.__process_sub_query(sub_query, scraped_data)
                for sub_query in sub_queries
            ]
        )
        return context

    async def __process_sub_query_with_vectorstore(self, sub_query: str, filter: Optional[dict] = None):
        """Takes in a sub query and gathers context from the user provided vector store

        Args:
            sub_query (str): The sub-query generated from the original query

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

        content = await self.researcher.context_manager.get_similar_content_by_query_with_vectorstore(sub_query, filter)

        if content and self.researcher.verbose:
            await stream_output(
                "logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket
            )
        elif self.researcher.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 No content found for '{sub_query}'...",
                self.researcher.websocket,
            )
        return content

    async def __process_sub_query(self, sub_query: str, scraped_data: list = []):
        """Takes in a sub query and scrapes urls based on it and gathers context.

        Args:
            sub_query (str): The sub-query generated from the original query
            scraped_data (list): Scraped data passed in

        Returns:
            str: The context gathered from search
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.researcher.websocket,
            )

        if not scraped_data:
            scraped_data = await self.__scrape_data_by_query(sub_query)

        content = await self.researcher.context_manager.get_similar_content_by_query(sub_query, scraped_data)

        if content and self.researcher.verbose:
            await stream_output(
                "logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket
            )
        elif self.researcher.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 No content found for '{sub_query}'...",
                self.researcher.websocket,
            )
        return content

    async def __get_new_urls(self, url_set_input):
        """Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
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

    async def __scrape_data_by_query(self, sub_query):
        """
        Runs a sub-query across multiple retrievers and scrapes the resulting URLs.

        Args:
            sub_query (str): The sub-query to search for.

        Returns:
            list: A list of scraped content results.
        """
        new_search_urls = []

        # Iterate through all retrievers
        for retriever_class in self.researcher.retrievers:
            # Instantiate the retriever with the sub-query
            retriever = retriever_class(sub_query)

            # Perform the search using the current retriever
            search_results = await asyncio.to_thread(
                retriever.search, max_results=self.researcher.cfg.max_search_results_per_query
            )

            # Collect new URLs from search results
            search_urls = [url.get("href") for url in search_results]
            new_search_urls.extend(search_urls)

        # Get unique URLs
        new_search_urls = await self.__get_new_urls(new_search_urls)
        random.shuffle(new_search_urls)

        # Log the research process if verbose mode is on
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "researching",
                f"🤔 Researching for relevant information across multiple sources...\n",
                self.researcher.websocket,
            )

        # Scrape the new URLs
        scraped_content = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store:
            self.researcher.vector_store.load(scraped_content)

        return scraped_content

    async def get_sub_queries(self, query):
        await stream_output(
            "logs",
            "planning_research",
            f"🌐 Browsing the web and planning research for query: {query}...",
            self.researcher.websocket,
        )

        return await get_sub_queries(
            query=query,
            retriever=self.researcher.retrievers[0],
            agent_role_prompt=self.researcher.role,
            cfg=self.researcher.cfg,
            parent_query=self.researcher.parent_query,
            report_type=self.researcher.report_type,
            cost_callback=self.researcher.add_costs,
        )
