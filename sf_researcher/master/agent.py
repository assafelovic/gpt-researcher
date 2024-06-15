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
            await stream_output("\nlogs", self.agent, self.websocket)

        sub_queries = self.custom_sub_query

        # gather raw context
        scraped_content_results = await asyncio.gather(*[self.scrape_sites_by_query(sub_query) for sub_query in sub_queries])
        documents = self.pinecone_manager.process_scraped_content(scraped_content_results)
        logger.info(f"\n🧩 agent.py pinecone insert results: \n{documents}\n")
        self.pinecone_manager.insert_documents(documents)
        time.sleep(2)

    async def conduct_research_query(self, query_list):
        """
    Queries the Pinecone index for relevant context based on the list of queries
    """
        aggregated_context = []
        for query in query_list:
            # Get context by similarity search for each query
            raw_context = self.pinecone_manager.query_documents(query)
            context_for_query = [doc.page_content for doc in raw_context]
            logger.info(f"\n🧩 agent.py conduct_research_query query: {query}:\n")
            for doc in raw_context:
                print(f"🌐 Document source: {doc.metadata['source']}")
                print(f"📑 Document content: {doc.page_content}\n")
            aggregated_context.extend(context_for_query)
            time.sleep(2)

        # Aggregate all contexts into one
        self.context = aggregated_context
        logger.info(f"\n🧩 Aggregated self.context: {self.context}\n")

    async def write_report(self):
        """
        Writes the report based on research conducted

        Returns:
            str: The report
        """
        if self.verbose:
            await stream_output("logs", f"✍️ Writing summary for research task: {self.query}...", self.websocket)

        report = await generate_report(self)

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
        new_search_urls = await self.get_new_urls([url.get("href") for url in search_results])

        # Scrape Urls
        if self.verbose:
            await stream_output("logs", f"🤔 Scraping sites for relevant information...\n", self.websocket)
        scraped_content_results = scrape_urls(new_search_urls, self.cfg)
        logger.info(f"\n🌐 scrape_urls content results for sub-query '{sub_query}':\n {scraped_content_results}\n")

        # updated_search_results = []
        # for search_result in search_results:
        #     url = search_result['href']
        #     matching_content = next((content for content in scraped_content_results if content['url'] == url), None)
        #     if matching_content:
        #         search_result['raw_content'] = matching_content['raw_content']
        #         updated_search_results.append(search_result)

        # logger.info(f"\n📦 updated_search_results: \n{updated_search_results}\n")
        # return updated_search_results

        return scraped_content_results
