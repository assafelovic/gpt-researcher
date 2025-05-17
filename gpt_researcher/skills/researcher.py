import asyncio
import random
import logging
import os
from ..actions.utils import stream_output
from ..actions.query_processing import plan_research_outline, get_search_results
from ..document import DocumentLoader, OnlineDocumentLoader, LangChainDocumentLoader
from ..utils.enum import ReportSource, ReportType
from ..utils.logging_config import get_json_handler
from ..actions.agent_creator import choose_agent


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

        # Check if any of the retrievers is an MCP retriever
        has_mcp_retriever = any("mcpretriever" in r.__name__.lower() for r in self.researcher.retrievers)
        
        # Check if we have proper MCP configurations in the headers
        has_mcp_configs = False
        if has_mcp_retriever:
            # Look for MCP-specific configuration keys in headers
            mcp_config_keys = [key for key in self.researcher.headers.keys() if key.startswith('mcp_')]
            has_mcp_configs = len(mcp_config_keys) > 0
            if not has_mcp_configs:
                self.logger.warning("MCP retriever specified but no MCP configurations found in headers")
        
        # If using MCP retrievers exclusively or with others, use the specialized web research handler
        if has_mcp_retriever and has_mcp_configs:
            self.logger.info("Using MCP-enabled web research")
            research_data = await self._conduct_web_research()
        # Otherwise, continue with standard research flow
        else:
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
                research_data = self.researcher.prompt_family.join_local_web_documents(docs_context, web_context)

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

    async def _conduct_web_research(self):
        """
        Conducts research on the web using the search retriever specified.
        """
        query = self.researcher.query
        retrievers = self.researcher.retrievers
        retriever_names = [r.__name__.lower() for r in retrievers]
        
        # Skip web search for MCP if it's the only retriever
        mcp_only = (len(retrievers) == 1 and "mcpretriever" in retriever_names[0].lower())

        initial_search_results = []
        
        # Skip initial search for MCP-only scenario
        if not mcp_only:
            # Default to the first retriever for initial search (typically TavilySearch)
            initial_search_results = await self._search(
                retriever=retrievers[0],
                query=query,
            )

        # If we have multiple retrievers including MCP, we'll use them all later

        # Choose agent and role
        if not (self.researcher.agent and self.researcher.role):
            self.researcher.agent, self.researcher.role = await choose_agent(
                query=query,
                cfg=self.researcher.cfg,
                parent_query=self.researcher.parent_query,
                cost_callback=self.researcher.add_costs,
                headers=self.researcher.headers,
                prompt_family=self.researcher.prompt_family
            )

        # Plan the research outline by generating sub-queries from initial search or query
        # For MCP, we'll use a special flow
        sub_queries = await plan_research_outline(
            query=query,
            search_results=initial_search_results,
            agent_role_prompt=self.researcher.role,
            cfg=self.researcher.cfg,
            parent_query=self.researcher.parent_query,
            report_type=self.researcher.report_type,
            cost_callback=self.researcher.add_costs,
            retriever_names=retriever_names,
        )

        if self.researcher.cfg.verbose:
            print(f"\n\nResearch questions: {sub_queries}\n")

        # Track progress
        await self._update_search_progress(0, len(sub_queries))

        # Research each sub-query and aggregate results
        context = []
        
        # If using MCP only, we'll do a direct retrieval with the MCP retriever
        if mcp_only:
            mcp_retriever = retrievers[0]
            mcp_results = await self._search(
                retriever=mcp_retriever,
                query=query,
            )
            
            # Process MCP results and add to context
            for result in mcp_results:
                context.append({
                    "content": result["body"],
                    "url": result["href"],
                    "query": query
                })
        else:
            # For traditional research or mixed MCP+web research, process each sub-query
            for i, sub_query in enumerate(sub_queries):
                if (
                    self.researcher.report_type == ReportType.DetailedReport.value
                    or self.researcher.report_type == ReportType.SubtopicReport.value
                ):
                    search_query = sub_query
                else:
                    search_query = sub_query
                
                # Search across all retrievers for this sub-query
                for retriever in retrievers:
                    retriever_search_results = await self._search(
                        retriever=retriever,
                        query=search_query,
                    )
                    
                    # If no results, try next retriever
                    if not retriever_search_results:
                        continue
                    
                    # For non-MCP retrievers, do content extraction and summarization
                    if "mcpretriever" not in retriever.__name__.lower():
                        # Extract content from search results
                        extracted_content = await self._extract_content(
                            results=retriever_search_results,
                        )
                        
                        # Summarize content if there's anything to summarize
                        if extracted_content:
                            summary = await self._summarize_content(
                                query=search_query,
                                content=extracted_content,
                            )
                            
                            # Add to research context
                            context.append({
                                "content": summary,
                                "query": search_query,
                                "url": [
                                    result["url"]
                                    for result in extracted_content
                                    if "url" in result
                                ],
                            })
                    else:
                        # For MCP retriever, directly add results to context
                        for result in retriever_search_results:
                            context.append({
                                "content": result["body"],
                                "url": result["href"],
                                "query": search_query
                            })
                    
                # Update research progress
                await self._update_search_progress(i + 1, len(sub_queries))

        return context

    async def _get_context_by_urls(self, urls):
        """Scrapes and compresses the context from the given urls"""
        self.logger.info(f"Getting context from URLs: {urls}")
        
        new_search_urls = await self._get_new_urls(urls)
        self.logger.info(f"New URLs to process: {new_search_urls}")

        scraped_content = await self.researcher.scraper_manager.browse_urls(new_search_urls)
        self.logger.info(f"Scraped content from {len(scraped_content)} URLs")

        if self.researcher.vector_store:
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
            context = await asyncio.gather(
                *[
                    self._process_sub_query(sub_query, scraped_data, query_domains)
                    for sub_query in sub_queries
                ]
            )
            self.logger.info(f"Gathered context from {len(context)} sub-queries")
            # Filter out empty results and join the context
            context = [c for c in context if c]
            if context:
                combined_context = " ".join(context)
                self.logger.info(f"Combined context size: {len(combined_context)}")
                return combined_context
            return []
        except Exception as e:
            self.logger.error(f"Error during web search: {e}", exc_info=True)
            return []

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
            if not scraped_data:
                scraped_data = await self._scrape_data_by_urls(sub_query, query_domains)
                self.logger.info(f"Scraped data size: {len(scraped_data)}")

            content = await self.researcher.context_manager.get_similar_content_by_query(sub_query, scraped_data)
            self.logger.info(f"Content found for sub-query: {len(str(content)) if content else 0} chars")

            if not content and self.researcher.verbose:
                await stream_output(
                    "logs",
                    "subquery_context_not_found",
                    f"🤷 No content found for '{sub_query}'...",
                    self.researcher.websocket,
                )
            if content:
                if self.json_handler:
                    self.json_handler.log_event("content_found", {
                        "sub_query": sub_query,
                        "content_size": len(content)
                    })
            return content
        except Exception as e:
            self.logger.error(f"Error processing sub-query {sub_query}: {e}", exc_info=True)
            return ""

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
        new_search_urls = []
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

            # Collect new URLs from search results
            search_urls = [url.get("href") for url in search_results]
            new_search_urls.extend(search_urls)

        # Get unique URLs
        new_search_urls = await self._get_new_urls(new_search_urls)
        random.shuffle(new_search_urls)

        return new_search_urls

    async def _scrape_data_by_urls(self, sub_query, query_domains: list | None = None):
        """
        Runs a sub-query across multiple retrievers and scrapes the resulting URLs.

        Args:
            sub_query (str): The sub-query to search for.

        Returns:
            list: A list of scraped content results.
        """
        if query_domains is None:
            query_domains = []

        new_search_urls = await self._search_relevant_source_urls(sub_query, query_domains)

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

    async def _search(self, retriever, query):
        """
        Perform a search using the specified retriever.
        
        Args:
            retriever: The retriever class to use
            query: The search query
            
        Returns:
            list: Search results
        """
        self.logger.info(f"Searching with {retriever.__name__} for query: {query}")
        
        try:
            # Instantiate the retriever
            retriever_instance = retriever(
                query=query, 
                headers=self.researcher.headers,
                query_domains=self.researcher.query_domains
            )
            
            # Perform the search
            if hasattr(retriever_instance, 'search'):
                results = retriever_instance.search(
                    max_results=self.researcher.cfg.max_search_results_per_query
                )
                return results
            else:
                self.logger.error(f"Retriever {retriever.__name__} does not have a search method")
                return []
        except Exception as e:
            self.logger.error(f"Error searching with {retriever.__name__}: {str(e)}")
            return []
            
    async def _extract_content(self, results):
        """
        Extract content from search results using the browser manager.
        
        Args:
            results: Search results
            
        Returns:
            list: Extracted content
        """
        self.logger.info(f"Extracting content from {len(results)} search results")
        
        # Get the URLs from the search results
        urls = []
        for result in results:
            if isinstance(result, dict) and "href" in result:
                urls.append(result["href"])
        
        # Skip if no URLs found
        if not urls:
            return []
            
        # Make sure we don't visit URLs we've already visited
        new_urls = [url for url in urls if url not in self.researcher.visited_urls]
        
        # Return empty if no new URLs
        if not new_urls:
            return []
            
        # Scrape the content from the URLs
        scraped_content = await self.researcher.scraper_manager.browse_urls(new_urls)
        
        # Add the URLs to visited_urls
        self.researcher.visited_urls.update(new_urls)
        
        return scraped_content
        
    async def _summarize_content(self, query, content):
        """
        Summarize the extracted content.
        
        Args:
            query: The search query
            content: The extracted content
            
        Returns:
            str: Summarized content
        """
        self.logger.info(f"Summarizing content for query: {query}")
        
        # Skip if no content
        if not content:
            return ""
            
        # Summarize the content using the context manager
        summary = await self.researcher.context_manager.get_similar_content_by_query(
            query, content
        )
        
        return summary
        
    async def _update_search_progress(self, current, total):
        """
        Update the search progress.
        
        Args:
            current: Current number of sub-queries processed
            total: Total number of sub-queries
        """
        if self.researcher.verbose and self.researcher.websocket:
            progress = int((current / total) * 100)
            await stream_output(
                "logs",
                "research_progress",
                f"📊 Research Progress: {progress}%",
                self.researcher.websocket,
                True,
                {
                    "current": current,
                    "total": total,
                    "progress": progress
                }
            )
