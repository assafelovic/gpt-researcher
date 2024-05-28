# agent.py

import asyncio
import time

from sf_researcher.config import Config
from sf_researcher.master.functions import *
from sf_researcher.memory import Memory
from sf_researcher.utils.enum import ReportType
from sf_researcher.utils.validators import *

from sf_researcher.context.pinecone_utils import PineconeManager

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SFResearcher:
    """
    SF Researcher
    """

    def __init__(
        self,
        query: str,
        namespace: str,
        index_name: str,
        report_type: str = ReportType.ResearchReport.value,
        source_urls=None,
        config_path=None,
        websocket=None,
        agent=None,
        role=None,
        parent_query: str = "",
        subtopics: list = [],
        visited_urls: set = set(),
        verbose: bool = True,
        custom_sub_queries: list = [],
        include_domains: list = [],
        exclude_domains: list = [],
        parent_sub_queries=None,
        child_sub_queries=None
    ):
        """
        Initialize the GPT Researcher class.
        Args:
            query: str,
            report_type: str
            source_urls
            config_path
            websocket
            agent
            role
            parent_query: str
            subtopics: list
            visited_urls: set
        """
        self.query = query
        self.agent = agent
        self.role = role
        self.report_type = report_type
        self.report_prompt = get_prompt_by_report_type(self.report_type)  # this validates the report type
        self.websocket = websocket
        self.cfg = Config(config_path)
        self.retriever = get_retriever(self.cfg.retriever)
        self.context = []
        self.source_urls = source_urls
        self.memory = Memory(self.cfg.embedding_provider)
        self.visited_urls = visited_urls
        self.verbose = verbose

        # Only relevant for DETAILED REPORTS
        # --------------------------------------

        # Stores the main query of the detailed report
        self.parent_query = parent_query

        # Stores all the user provided subtopics
        self.subtopics = subtopics
        self.custom_sub_query = custom_sub_queries
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains
        self.pinecone_manager = PineconeManager(index_name, self.memory.get_embeddings(), namespace)
        self.parent_sub_queries = parent_sub_queries
        self.child_sub_queries = child_sub_queries

    async def conduct_research_insert(self):
        """
        Runs the GPT Researcher to conduct research
        """
        if self.verbose:
            await stream_output("logs", f"🔎 Starting the research task for '{self.query}'...", self.websocket)
        
        # Generate Agent
        self.agent, self.role = ("Compliance Agent", "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text.")

        if self.verbose:
            await stream_output("logs", self.agent, self.websocket)

        # self.context = await self.get_context_by_search(self.query)
        sub_queries = self.custom_sub_query

        # gather raw context
        scraped_content_results = await asyncio.gather(*[self.scrape_sites_by_query(sub_query) for sub_query in sub_queries])
        documents = self.pinecone_manager.process_scraped_content(scraped_content_results)
        logger.info(f"pinecone procssed content results: {documents}")
        self.pinecone_manager.insert_documents(documents)
        time.sleep(2)

    async def conduct_research_directors(self):
        # Get list of all directors
        if not self.directors:
            logger.info(f"Constructing directors using construct_directors function")
            self.directors = await construct_directors(
                task=self.query,
                data=self.context,
                config=self.cfg,
            )
        else:
            logger.info("Using the provided directors list")
        
        logger.info("Directors **** : %s", self.directors)


    async def conduct_research_query(self):
        """
        Queries the Pinecone index for relevant context based on the query
        """

        #get context by similarity search
        raw_context = self.pinecone_manager.query_documents(self.query)
        self.context = [doc.page_content for doc in raw_context]
        time.sleep(2)

    async def write_report(self, existing_headers: list = []):
        """
        Writes the report based on research conducted

        Returns:
            str: The report
        """
        if self.verbose:
            await stream_output("logs", f"✍️ Writing summary for research task: {self.query}...", self.websocket)

        if self.report_type == "custom_report":
            self.role = self.cfg.agent_role if self.cfg.agent_role else self.role
        elif self.report_type == "director_report":
            report = await generate_report(
                query=self.query,
                context=self.context,
                agent_role_prompt=self.role,
                report_type=self.report_type,
                cfg=self.cfg,
                main_topic=self.parent_query,
                existing_headers=existing_headers
            )
        else:
            report = await generate_report(
                query=self.query,
                context=self.context,
                agent_role_prompt=self.role,
                report_type=self.report_type,
                websocket=self.websocket,
                cfg=self.cfg
            )

        return report

    async def get_context_by_urls(self, urls):
        """
            Scrapes and compresses the context from the given urls
        """
        new_search_urls = await self.get_new_urls(urls)
        if self.verbose:
            await stream_output("logs",
                            f"🧠 I will conduct my research based on the following urls: {new_search_urls}...",
                            self.websocket)
        scraped_sites = scrape_urls(new_search_urls, self.cfg)
        return await self.get_similar_content_by_query(self.query, scraped_sites)

    async def get_context_by_search(self, query):
        """
           Generates the context for the research task by searching the query and scraping the results
        Returns:
            context: List of context
        """
        context = []
        # Generate Sub-Queries including original query
        if self.custom_sub_query:
            sub_queries = self.custom_sub_query
        else:
            if self.verbose:
                await stream_output("logs",
                                    f"🧠 I will now generate a list of sub queries from the main query: {self.parent_query}...",
                                    self.websocket)
            sub_queries = await get_sub_queries(query, self.role, self.cfg, self.parent_query, self.report_type)

        if self.verbose:
            await stream_output("logs",
                                f"🧠 I will conduct my research based on the following queries: {sub_queries}...",
                                self.websocket)

        # Using asyncio.gather to process the sub_queries asynchronously
        context = await asyncio.gather(*[self.process_sub_query(sub_query) for sub_query in sub_queries])
        return context

    async def get_new_urls(self, url_set_input):
        """ Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                new_urls.append(url)
                if self.verbose:
                    await stream_output("logs", f"✅ Added source url to research: {url}\n", self.websocket)

        return new_urls

    async def scrape_sites_by_query(self, sub_query):
        """
        Runs a sub-query
        Args:
            sub_query:

        Returns:
            Summary
        """
        # Get Urls
        if self.cfg.retriever == "tavily":
            retriever = self.retriever(sub_query, include_domains=self.include_domains, exclude_domains=self.exclude_domains)
        else:
            retriever = self.retriever(sub_query)
        search_results = retriever.search(
            max_results=self.cfg.max_search_results_per_query)
        new_search_urls = await self.get_new_urls([url.get("url") for url in search_results])

        logger.info(f"get_new_urls parsed results: {new_search_urls}")
        # Scrape Urls
        if self.verbose:
            await stream_output("logs", f"🤔 Researching for relevant information...\n", self.websocket)
        scraped_content_results = scrape_urls(new_search_urls, self.cfg)
        logger.info(f"Scraped content results for sub-query '{sub_query}': {scraped_content_results}")

        updated_search_results = []
        for search_result in search_results:
            url = search_result['url']
            matching_content = next((content for content in scraped_content_results if content['url'] == url), None)
            if matching_content:
                search_result['raw_content'] = matching_content['raw_content']
                updated_search_results.append(search_result)

        logger.info(f"updated_search_results: {updated_search_results}")
        return updated_search_results
