import asyncio
import random
import logging
import os
from ..actions.utils import stream_output
from ..actions.query_processing import plan_research_outline, get_search_results
from ..document import DocumentLoader, OnlineDocumentLoader, LangChainDocumentLoader
from ..utils.enum import ReportSource
from ..utils.logging_config import get_json_handler


class ResearchConductor:
    """Manages and coordinates the research process."""

    def __init__(self, researcher):
        self.researcher = researcher
        self.logger = logging.getLogger('research')
        self.json_handler = get_json_handler()

    async def plan_research(self, query, query_domains=None):
        self.logger.info(f"Planning research for query: {query}")
        if query_domains:
            self.logger.info(f"Query domains: {query_domains}")
        
        await stream_output(
            "logs",
            "planning_research",
            f"🌐 Browsing the web to learn more about the task: {query}...",
            self.researcher.websocket,
        )

        search_results = await get_search_results(query, self.researcher.retrievers[0], query_domains)
        self.logger.info(f"Initial search results obtained: {len(search_results)} results")

        await stream_output(
            "logs",
            "planning_research",
            f"🤔 Planning the research strategy and subtasks...",
            self.researcher.websocket,
        )

        outline = await plan_research_outline(
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

    async def conduct_research(self):
        """Runs the GPT Researcher to conduct research"""
        if self.json_handler:
            self.json_handler.update_content("query", self.researcher.query)
        
        self.logger.info(f"Starting research for query: {self.researcher.query}")
        
        # Reset visited_urls and source_urls at the start of each research task
        self.researcher.visited_urls.clear()
        research_data = []

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "starting_research",
                f"🔍 Starting the research task for '{self.researcher.query}'...",
                self.researcher.websocket,
            )
            await stream_output(
                "logs",
                "agent_generated",
                self.researcher.agent,
                self.researcher.websocket
            )

        # Research for relevant sources based on source types below
        if self.researcher.source_urls:
            self.logger.info("Using provided source URLs")
            research_data = await self._get_context_by_urls(self.researcher.source_urls)
            if research_data and len(research_data) == 0 and self.researcher.verbose:
                await stream_output(
                    "logs",
                    "answering_from_memory",
                    f"🧐 I was unable to find relevant context in the provided sources...",
                    self.researcher.websocket,
                )
            if self.researcher.complement_source_urls:
                self.logger.info("Complementing with web search")
                additional_research = await self._get_context_by_web_search(self.researcher.query, [], self.researcher.query_domains)
                research_data += ' '.join(additional_research)

        elif self.researcher.report_source == ReportSource.Web.value:
            self.logger.info("Using web search")
            research_data = await self._get_context_by_web_search(self.researcher.query, [], self.researcher.query_domains)

        elif self.researcher.report_source == ReportSource.Local.value:
            self.logger.info("Using local search")
            document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
            self.logger.info(f"Loaded {len(document_data)} documents")
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)

            research_data = await self._get_context_by_web_search(self.researcher.query, document_data, self.researcher.query_domains)

        # Hybrid search including both local documents and web sources
        elif self.researcher.report_source == ReportSource.Hybrid.value:
            if self.researcher.document_urls:
                document_data = await OnlineDocumentLoader(self.researcher.document_urls).load()
            else:
                document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)
            docs_context = await self._get_context_by_web_search(self.researcher.query, document_data, self.researcher.query_domains)
            web_context = await self._get_context_by_web_search(self.researcher.query, [], self.researcher.query_domains)
            research_data = f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"

        elif self.researcher.report_source == ReportSource.Azure.value:
            from ..document.azure_document_loader import AzureDocumentLoader
            azure_loader = AzureDocumentLoader(
                container_name=os.getenv("AZURE_CONTAINER_NAME"),
                connection_string=os.getenv("AZURE_CONNECTION_STRING")
            )
            azure_files = await azure_loader.load()
            document_data = await DocumentLoader(azure_files).load()  # Reuse existing loader
            research_data = await self._get_context_by_web_search(self.researcher.query, document_data)
            
        elif self.researcher.report_source == ReportSource.LangChainDocuments.value:
            langchain_documents_data = await LangChainDocumentLoader(
                self.researcher.documents
            ).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(langchain_documents_data)
            research_data = await self._get_context_by_web_search(
                self.researcher.query, langchain_documents_data, self.researcher.query_domains
            )

        elif self.researcher.report_source == ReportSource.LangChainVectorStore.value:
            research_data = await self._get_context_by_vectorstore(self.researcher.query, self.researcher.vector_store_filter)

        # Rank and curate the sources
        self.researcher.context = research_data
        if self.researcher.cfg.curate_sources:
            self.logger.info("Curating sources")
            self.researcher.context = await self.researcher.source_curator.curate_sources(research_data)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_step_finalized",
                f"Finalized research step.\n💸 Total Research Costs: ${self.researcher.get_costs()}",
                self.researcher.websocket,
            )
            if self.json_handler:
                self.json_handler.update_content("costs", self.researcher.get_costs())
                self.json_handler.update_content("context", self.researcher.context)

        self.logger.info(f"Research completed. Context size: {len(str(self.researcher.context))}")
        return self.researcher.context

    async def _get_context_by_urls(self, urls):
        """Scrapes and compresses the context from the given urls"""
        self.logger.info(f"Getting context from URLs: {urls}")
        
        new_search_urls = await self._get_new_urls(urls)
        self.logger.info(f"New URLs to process: {new_search_urls}")

        scraped_content = await self.researcher.scraper_manager.browse_urls(new_search_urls)
        self.logger.info(f"Scraped content from {len(scraped_content)} URLs")

        if self.researcher.vector_store:
            self.logger.info("Loading content into vector store")
            self.researcher.vector_store.load(scraped_content)

        context = await self.researcher.context_manager.get_similar_content_by_query(
            self.researcher.query, scraped_content
        )
        return context

    # Add logging to other methods similarly...

    async def _get_context_by_vectorstore(self, query, filter: dict | None = None):
        """
        Generates the context for the research task by searching the vectorstore
        Returns:
            context: List of context
        """
        self.logger.info(f"Starting vectorstore search for query: {query}")
        context = []
        # Generate Sub-Queries including original query
        sub_queries = await self.plan_research(query)
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

    async def _get_context_by_web_search(self, query, scraped_data: list | None = None, query_domains: list | None = None):
        """
        Generates the context for the research task by searching the query and scraping the results
        Returns:
            context: List of context
        """
        self.logger.info(f"Starting web search for query: {query}")
        
        if scraped_data is None:
            scraped_data = []
        if query_domains is None:
            query_domains = []

        # Generate Sub-Queries including original query
        sub_queries = await self.plan_research(query, query_domains)
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
            # context will be a list of lists of dictionaries
            # e.g., [[{src1_q1}, {src2_q1}], [{src1_q2}], []]
            context_per_sub_query = await asyncio.gather(
                *[
                    self._process_sub_query(sub_query, scraped_data if i == 0 else [], query_domains) # Pass scraped_data only to the first sub_query
                    for i, sub_query in enumerate(sub_queries)
                ]
            )
            self.logger.info(f"Gathered results from {len(context_per_sub_query)} sub-queries.")

            # Flatten the list of lists into a single list of dictionaries
            # and filter out any None items that might result from errors in _process_sub_query
            all_sources = [item for sublist in context_per_sub_query if sublist for item in sublist if item]
            
            # Remove duplicate sources based on 'href' or a unique ID if available, preserving order
            # This is a simple way to deduplicate if retrievers return overlapping results for different sub-queries
            seen_hrefs = set()
            unique_sources = []
            for source in all_sources:
                href = source.get('href')
                if href and href not in seen_hrefs:
                    unique_sources.append(source)
                    seen_hrefs.add(href)
                elif not href: # Keep sources without href for now, or decide on a different ID
                    unique_sources.append(source)


            self.logger.info(f"Total unique sources found: {len(unique_sources)}")
            return unique_sources # Return the list of dictionaries
        except Exception as e:
            self.logger.error(f"Error during web search: {e}", exc_info=True)
            return [] # Return empty list on error

    async def _process_sub_query(self, sub_query: str, scraped_data: list = [], query_domains: list = []):
        """Takes in a sub query and scrapes urls based on it and gathers context."""
        if self.json_handler:
            self.json_handler.log_event("sub_query", {
                "query": sub_query,
                "scraped_data_size": len(scraped_data)
            })
        
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.researcher.websocket,
            )

        try:
            enriched_sources = []
            if not scraped_data: # If no pre-scraped data is provided
                enriched_sources = await self._scrape_data_by_urls(sub_query, query_domains)
                self.logger.info(f"Scraped and enriched {len(enriched_sources)} sources for sub-query '{sub_query}'.")
            else: # If pre-scraped data is provided (e.g. from a main query's initial scrape)
                # This path assumes scraped_data is already in the enriched format (list of dicts)
                # If it's not, this part of the logic might need adjustment based on what _get_context_by_web_search passes.
                # For now, assuming it's already enriched or doesn't need further processing if passed.
                # The plan implies scraped_data might be empty or the result of _scrape_data_by_urls.
                # So, if scraped_data is provided, it's already the "enriched_sources".
                enriched_sources = scraped_data 
                self.logger.info(f"Using {len(enriched_sources)} provided sources for sub-query '{sub_query}'.")

            # The plan is to return the list of dictionaries directly.
            # The summarization/similarity search previously done by get_similar_content_by_query
            # will be handled differently or by the SourceCurator/ReportGenerator.
            
            if not enriched_sources and self.researcher.verbose:
                 await stream_output(
                    "logs",
                    "subquery_sources_not_found", # Changed log event name
                    f"🤷 No sources found or scraped for '{sub_query}'...",
                    self.researcher.websocket,
                )
            
            if enriched_sources and self.json_handler:
                self.json_handler.log_event("sources_processed_for_sub_query", { # Changed log event name
                    "sub_query": sub_query,
                    "num_sources": len(enriched_sources)
                })
            return enriched_sources
        except Exception as e:
            self.logger.error(f"Error processing sub-query {sub_query}: {e}", exc_info=True)
            return [] # Return empty list on error

    async def _process_sub_query_with_vectorstore(self, sub_query: str, filter: dict | None = None):
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

        context = await self.researcher.context_manager.get_similar_content_by_query_with_vectorstore(sub_query, filter)

        return context

    async def _get_new_urls(self, url_set_input):
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

    async def _search_relevant_source_urls(self, query, query_domains: list | None = None):
        full_search_results = []
        if query_domains is None:
            query_domains = []

        # Iterate through all retrievers
        for retriever_class in self.researcher.retrievers:
            # Instantiate the retriever with the sub-query
            retriever = retriever_class(query, query_domains=query_domains)

            # Perform the search using the current retriever
            search_results = await asyncio.to_thread(
                retriever.search, max_results=self.researcher.cfg.max_search_results_per_query
            )
            if search_results:
                full_search_results.extend(search_results)

        # Extract hrefs and get unique new hrefs
        hrefs = [res.get("href") for res in full_search_results if res.get("href")]
        unique_new_hrefs = await self._get_new_urls(hrefs)
        
        # Filter full_search_results to keep only those whose 'href' is in unique_new_hrefs
        filtered_results = [res for res in full_search_results if res.get("href") in unique_new_hrefs]
        
        random.shuffle(filtered_results)

        return filtered_results

    async def _scrape_data_by_urls(self, sub_query, query_domains: list | None = None):
        """
        Runs a sub-query across multiple retrievers, scrapes the resulting URLs,
        and enriches the initial retriever outputs with scraped content.

        Args:
            sub_query (str): The sub-query to search for.
            query_domains (list | None): Optional list of domains to query.

        Returns:
            list: A list of enriched dictionaries, where each dictionary is a retriever
                  output augmented with 'raw_content' and 'scraped_title'.
        """
        if query_domains is None:
            query_domains = []

        retriever_outputs = await self._search_relevant_source_urls(sub_query, query_domains)
        urls_to_scrape = [item.get('href') for item in retriever_outputs if item.get('href')]

        # Log the research process if verbose mode is on
        if self.researcher.verbose and urls_to_scrape:
            await stream_output(
                "logs",
                "researching",
                f"🤔 Researching for relevant information from {len(urls_to_scrape)} URLs...\n",
                self.researcher.websocket,
            )

        # Scrape the new URLs
        # scraped_pages is expected to be a list of dicts, each like 
        # {'url': '...', 'raw_content': '...', 'title': '...' (optional), ...}
        scraped_pages = await self.researcher.scraper_manager.browse_urls(urls_to_scrape)
        
        scraped_content_map = {page['url']: page for page in scraped_pages if page.get('url')}

        enriched_outputs = []
        for item in retriever_outputs:
            href = item.get('href')
            if href:
                scraped_page_data = scraped_content_map.get(href)
                if scraped_page_data:
                    item['raw_content'] = scraped_page_data.get('raw_content') # In Scraper, content is under raw_content
                    if 'title' in scraped_page_data:
                         item['scraped_title'] = scraped_page_data.get('title')
                enriched_outputs.append(item) # Add item even if not scraped, to keep all sources

        if self.researcher.vector_store and enriched_outputs:
            # Assuming vector_store.load expects a list of dicts with 'raw_content'
            # We might need to adapt what we pass to vector_store.load if it expects a different format
            # For now, passing the enriched outputs directly if they have 'raw_content'
            # Or consider passing only scraped_pages if that's what it's trained for.
            # Based on previous usage, it seems to expect objects with 'raw_content'.
            
            # Filter items that have raw_content for vector store loading
            content_for_vector_store = [item for item in enriched_outputs if item.get('raw_content')]
            if content_for_vector_store:
                 self.researcher.vector_store.load(content_for_vector_store)


        return enriched_outputs
