import asyncio
import random
import time

from typing import Set

from gpt_researcher.config import Config
from gpt_researcher.context.compression import ContextCompressor, WrittenContentCompressor
from gpt_researcher.document import DocumentLoader, LangChainDocumentLoader
from gpt_researcher.master.actions import *
from gpt_researcher.memory import Memory
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone


class GPTResearcher:
    """
    GPT Researcher
    """

    def __init__(
        self,
        query: str,
        report_type: str = ReportType.ResearchReport.value,
        report_source=ReportSource.Web.value,
        tone: Tone = Tone.Objective,
        source_urls=None,
        documents=None,
        config_path=None,
        websocket=None,
        agent=None,
        role=None,
        parent_query: str = "",
        subtopics: list = [],
        visited_urls: set = set(),
        verbose: bool = True,
        context=[],
        headers: dict = None,  # Add headers parameter
    ):
        """
        Initialize the GPT Researcher class.
        Args:
            query: str,
            report_type: str
            source_urls
            tone
            config_path
            websocket
            agent
            role
            parent_query: str
            subtopics: list
            visited_urls: set
        """
        self.headers = headers or {}
        self.query: str = query
        self.agent: str = agent
        self.role: str = role
        self.report_type: str = report_type
        self.report_prompt: str = get_prompt_by_report_type(
            self.report_type
        )  # this validates the report type
        self.research_costs: float = 0.0
        self.cfg = Config(config_path)
        self.report_source: str = self.cfg.report_source or report_source
        self.retrievers = get_retrievers(self.headers, self.cfg)
        self.context = context
        self.source_urls = source_urls
        self.documents = documents
        self.memory = Memory(self.cfg.embedding_provider, self.headers)
        self.visited_urls: set[str] = visited_urls
        self.verbose: bool = verbose
        self.websocket = websocket
        self.headers = headers or {}
        # Ensure tone is an instance of Tone enum
        if isinstance(tone, dict):
            print(f"Invalid tone format: {tone}. Setting to default Tone.Objective.")
            self.tone = Tone.Objective
        elif isinstance(tone, str):
            self.tone = Tone[tone]
        else:
            self.tone = tone

        # Only relevant for DETAILED REPORTS
        # --------------------------------------

        # Stores the main query of the detailed report
        self.parent_query = parent_query

        # Stores all the user provided subtopics
        self.subtopics = subtopics

    async def conduct_research(self):
        """
        Runs the GPT Researcher to conduct research
        """
        # Reset visited_urls and source_urls at the start of each research task
        self.visited_urls.clear()
        if self.report_source != ReportSource.Sources.value:
            self.source_urls = []

        if self.verbose:
            await stream_output(
                "logs",
                "starting_research",
                f"🔎 Starting the research task for '{self.query}'...",
                self.websocket,
            )

        # Generate Agent
        if not (self.agent and self.role):
            self.agent, self.role = await choose_agent(
                query=self.query,
                cfg=self.cfg,
                parent_query=self.parent_query,
                cost_callback=self.add_costs,
                headers=self.headers,
            )

        if self.verbose:
            await stream_output("logs", "agent_generated", self.agent, self.websocket)

        # If specified, the researcher will use the given urls as the context for the research.
        if self.source_urls:
            self.context = await self.__get_context_by_urls(self.source_urls)

        elif self.report_source == ReportSource.Local.value:
            document_data = await DocumentLoader(self.cfg.doc_path).load()
            self.context = await self.__get_context_by_search(self.query, document_data)

        # Hybrid search including both local documents and web sources
        elif self.report_source == ReportSource.Hybrid.value:
            document_data = await DocumentLoader(self.cfg.doc_path).load()
            docs_context = await self.__get_context_by_search(self.query, document_data)
            web_context = await self.__get_context_by_search(self.query)
            self.context = f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"

        elif self.report_source == ReportSource.LangChainDocuments.value:
            langchain_documents_data = await LangChainDocumentLoader(
                self.documents
            ).load()
            self.context = await self.__get_context_by_search(
                self.query, langchain_documents_data
            )

        # Default web based research
        else:
            self.context = await self.__get_context_by_search(self.query)

        time.sleep(2)
        if self.verbose:
            await stream_output(
                "logs",
                "research_step_finalized",
                f"Finalized research step.\n💸 Total Research Costs: ${self.get_costs()}",
                self.websocket,
            )

        return self.context

    async def write_report(self, existing_headers: list = [], relevant_written_contents: list = []):
        """
        Writes the report based on research conducted

        Returns:
            str: The report
        """
        report = ""

        if self.verbose:
            await stream_output(
                "logs",
                "task_summary_coming_up",
                f"✍️ Writing summary for research task: {self.query} (this may take a few minutes)...",
                self.websocket,
            )

        if self.report_type == "custom_report":
            self.role = self.cfg.agent_role if self.cfg.agent_role else self.role
            report = await generate_report(
                query=self.query,
                context=self.context,
                agent_role_prompt=self.role,
                report_type=self.report_type,
                report_source=self.report_source,
                tone=self.tone,
                websocket=self.websocket,
                cfg=self.cfg,
                headers=self.headers,
            )
        elif self.report_type == "subtopic_report":
            report = await generate_report(
                query=self.query,
                context=self.context,
                agent_role_prompt=self.role,
                report_type=self.report_type,
                report_source=self.report_source,
                websocket=self.websocket,
                tone=self.tone,
                cfg=self.cfg,
                main_topic=self.parent_query,
                existing_headers=existing_headers,
                relevant_written_contents=relevant_written_contents,
                cost_callback=self.add_costs,
                headers=self.headers,
            )
        else:
            report = await generate_report(
                query=self.query,
                context=self.context,
                agent_role_prompt=self.role,
                report_type=self.report_type,
                report_source=self.report_source,
                tone=self.tone,
                websocket=self.websocket,
                cfg=self.cfg,
                cost_callback=self.add_costs,
                headers=self.headers,
            )

        return report

    async def __get_context_by_urls(self, urls):
        """
        Scrapes and compresses the context from the given urls
        """
        new_search_urls = await self.__get_new_urls(urls)
        if self.verbose:
            await stream_output(
                "logs",
                "source_urls",
                f"🗂️ I will conduct my research based on the following urls: {new_search_urls}...",
                self.websocket,
            )

        scraped_sites = scrape_urls(new_search_urls, self.cfg)
        return await self.__get_similar_content_by_query(self.query, scraped_sites)

    async def __get_context_by_search(self, query, scraped_data: list = []):
        """
           Generates the context for the research task by searching the query and scraping the results
        Returns:
            context: List of context
        """
        context = []
        # Generate Sub-Queries including original query
        sub_queries = await get_sub_queries(
            query=query,
            agent_role_prompt=self.role,
            cfg=self.cfg,
            parent_query=self.parent_query,
            report_type=self.report_type,
            cost_callback=self.add_costs,
            openai_api_key=self.headers.get("openai_api_key"),
        )

        # If this is not part of a sub researcher, add original query to research for better results
        if self.report_type != "subtopic_report":
            sub_queries.append(query)

        if self.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️ I will conduct my research based on the following queries: {sub_queries}...",
                self.websocket,
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

    async def __process_sub_query(self, sub_query: str, scraped_data: list = []):
        """Takes in a sub query and scrapes urls based on it and gathers context.

        Args:
            sub_query (str): The sub-query generated from the original query
            scraped_data (list): Scraped data passed in

        Returns:
            str: The context gathered from search
        """
        if self.verbose:
            await stream_output(
                "logs",
                "running_subquery_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.websocket,
            )

        if not scraped_data:
            scraped_data = await self.__scrape_data_by_query(sub_query)

        content = await self.__get_similar_content_by_query(sub_query, scraped_data)

        if content and self.verbose:
            await stream_output(
                "logs", "subquery_context_window", f"📃 {content}", self.websocket
            )
        elif self.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 No content found for '{sub_query}'...",
                self.websocket,
            )
        return content

    async def __get_new_urls(self, url_set_input):
        """Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                new_urls.append(url)
                if self.verbose:
                    await stream_output(
                        "logs",
                        "added_source_url",
                        f"✅ Added source url to research: {url}\n",
                        self.websocket,
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
        for retriever_class in self.retrievers:
            # Instantiate the retriever with the sub-query
            retriever = retriever_class(sub_query)

            # Perform the search using the current retriever
            search_results = await asyncio.to_thread(
                retriever.search, max_results=self.cfg.max_search_results_per_query
            )

            # Collect new URLs from search results
            search_urls = [url.get("href") for url in search_results]
            new_search_urls.extend(search_urls)

        # Get unique URLs
        new_search_urls = await self.__get_new_urls(new_search_urls)
        random.shuffle(new_search_urls)

        # Log the research process if verbose mode is on
        if self.verbose:
            await stream_output(
                "logs",
                "researching",
                f"🤔 Researching for relevant information across multiple sources...\n",
                self.websocket,
            )

        # Scrape the new URLs
        scraped_content_results = await asyncio.to_thread(
            scrape_urls, new_search_urls, self.cfg
        )

        return scraped_content_results

    async def __get_similar_content_by_query(self, query, pages):
        if self.verbose:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"📚 Getting relevant content based on query: {query}...",
                self.websocket,
            )

        # Summarize Raw Data
        context_compressor = ContextCompressor(
            documents=pages, embeddings=self.memory.get_embeddings()
        )
        # Run Tasks
        return await context_compressor.async_get_context(
            query=query, max_results=8, cost_callback=self.add_costs
        )

    ########################################################################################

    # GETTERS & SETTERS
    def get_source_urls(self) -> list:
        return list(self.visited_urls)

    def get_research_context(self) -> list:
        return self.context

    def get_costs(self) -> float:
        return self.research_costs

    def set_verbose(self, verbose: bool):
        self.verbose = verbose

    def add_costs(self, cost: int) -> None:
        if not isinstance(cost, float) and not isinstance(cost, int):
            raise ValueError("Cost must be an integer or float")
        self.research_costs += cost

    ########################################################################################

    # DETAILED REPORT

    async def write_introduction(self):
        # Construct Report Introduction from main topic research
        introduction = await get_report_introduction(
            self.query,
            self.context,
            self.role,
            self.cfg,
            self.websocket,
            self.add_costs,
        )

        return introduction

    async def get_subtopics(self):
        """
        This async function generates subtopics based on user input and other parameters.

        Returns:
          The `get_subtopics` function is returning the `subtopics` that are generated by the
        `construct_subtopics` function.
        """
        if self.verbose:
            await stream_output(
                "logs",
                "generating_subtopics",
                f"🤔 Generating subtopics...",
                self.websocket,
            )

        subtopics = await construct_subtopics(
            task=self.query,
            data=self.context,
            config=self.cfg,
            # This is a list of user provided subtopics
            subtopics=self.subtopics,
        )

        if self.verbose:
            await stream_output(
                "logs", "subtopics", f"📋Subtopics: {subtopics}", self.websocket
            )

        return subtopics

    async def get_draft_section_titles(self):
        """
        Writes the draft section titles based on research conducted. The draft section titles are used to retrieve the previous relevant written contents.

        Returns:
            str: The headers markdown text
        """
        if self.verbose:
            await stream_output(
                "logs",
                "task_summary_coming_up",
                f"✍️ Writing draft section titles for research task: {self.query}...",
                self.websocket,
            )

        draft_section_titles = await generate_draft_section_titles(
            query=self.query,
            context=self.context,
            agent_role_prompt=self.role,
            report_type=self.report_type,
            websocket=self.websocket,
            cfg=self.cfg,
            main_topic=self.parent_query,
            cost_callback=self.add_costs,
            headers=self.headers,
        )

        return draft_section_titles
    
    async def __get_similar_written_contents_by_query(self,
            query: str,
            written_contents: List[Dict],
            similarity_threshold: float = 0.5,
            max_results: int = 10
        ) -> List[str]:
        """
        Asynchronously retrieves similar written contents based on a given query.

        Args:
            query (str): The query to search for similar written contents.
            written_contents (List[Dict]): List of written contents to search through.
            similarity_threshold (float, optional): The minimum similarity score for content to be considered relevant. 
                                                    Defaults to 0.5.
            max_results (int, optional): The maximum number of similar contents to return. Defaults to 10.

        Returns:
            List[str]: A list of similar written contents, limited by max_results.
        """
        if self.verbose:
            await stream_output(
                "logs",
                "fetching_relevant_written_content",
                f"🔎 Getting relevant written content based on query: {query}...",
                self.websocket,
            )

        # Retrieve similar written contents based on the query
        # Use a higher similarity threshold to ensure more relevant results and reduce irrelevant matches
        written_content_compressor = WrittenContentCompressor(
            documents=written_contents, embeddings=self.memory.get_embeddings(), similarity_threshold=similarity_threshold
        )
        return await written_content_compressor.async_get_context(
            query=query, max_results=max_results, cost_callback=self.add_costs
        )
    
    async def get_similar_written_contents_by_draft_section_titles(
        self, 
        current_subtopic: str, 
        draft_section_titles: List[str],
        written_contents: List[Dict],
        max_results: int = 10
    ) -> List[str]:
        """
        Retrieve similar written contents based on current subtopic and draft section titles.
        
        Args:
        current_subtopic (str): The current subtopic.
        draft_section_titles (List[str]): List of draft section titles.
        written_contents (List[Dict]): List of written contents to search through.
        max_results (int): Maximum number of results to return. Defaults to 10.
        
        Returns:
        List[str]: List of relevant written contents.
        """
        all_queries = [current_subtopic] + draft_section_titles
        
        async def process_query(query: str) -> Set[str]:
            return set(await self.__get_similar_written_contents_by_query(query, written_contents))

        # Run all queries in parallel
        results = await asyncio.gather(*[process_query(query) for query in all_queries])
        
        # Combine all results
        relevant_contents = set().union(*results)

        # Limit the number of results
        relevant_contents = list(relevant_contents)[:max_results]

        if relevant_contents and self.verbose:
            prettier_contents = "\n".join(relevant_contents)
            await stream_output(
                "logs", "relevant_contents_context", f"📃 {prettier_contents}", self.websocket
            )

        return relevant_contents