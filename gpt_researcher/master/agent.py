import time
from gpt_researcher.config import Config
from gpt_researcher.master.functions import *


class GPTResearcher:
    """
    GPT Researcher
    """
    def __init__(self, query, report_type, config_path=None, websocket=None):
        """
        Initialize the GPT Researcher class.
        Args:
            query:
            report_type:
            config_path:
            websocket:
        """
        self.query = query
        self.agent = None
        self.role = None
        self.report_type = report_type
        self.websocket = websocket
        self.cfg = Config(config_path)
        self.retriever = get_retriever(self.cfg.retriever)
        self.context = []
        self.visited_urls = set()

    async def run(self):
        """
        Runs the GPT Researcher
        Returns:
            Report
        """
        print(f"🔎 Running research for '{self.query}'...")
        # Generate Agent
        self.agent, self.role = await choose_agent(self.query, self.cfg)
        await stream_output("logs", self.agent, self.websocket)

        # Generate Sub-Queries including original query
        sub_queries = await get_sub_queries(self.query, self.role, self.cfg) + [self.query]
        await stream_output("logs",
                                 f"🧠 I will conduct my research based on the following queries: {sub_queries}...", self.websocket)

        # Run Sub-Queries
        for sub_query in sub_queries:
            await stream_output("logs", f"\n🔎 Running research for '{sub_query}'...", self.websocket)
            context = await self.run_sub_query(sub_query)
            self.context.append(context)

        # Conduct Research
        await stream_output("logs", f"✍️ Writing {self.report_type} for research task: {self.query}...", self.websocket)
        report = await generate_report(query=self.query, context=self.context,
                                       agent_role_prompt=self.role, report_type=self.report_type,
                                       websocket=self.websocket, cfg=self.cfg)
        time.sleep(2)
        return report

    async def get_new_urls(self, url_set_input):
        """ Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                await stream_output("logs", f"✅ Adding source url to research: {url}\n", self.websocket)

                self.visited_urls.add(url)
                new_urls.append(url)

        return new_urls

    async def run_sub_query(self, sub_query):
        """
        Runs a sub-query
        Args:
            sub_query:

        Returns:
            Summary
        """
        # Get Urls
        retriever = self.retriever(sub_query)
        search_results = retriever.search()
        new_search_urls = await self.get_new_urls([url.get("href") for url in search_results])

        # Scrape Urls
        await stream_output("logs", f"📝 Scraping urls {new_search_urls}...\n", self.websocket)
        content = scrape_urls(new_search_urls, self.cfg)
        await stream_output("logs", f"Researching for relevant information...\n", self.websocket)
        # Summarize Raw Data
        summary = await summarize(query=sub_query, content=content, agent_role_prompt=self.role, cfg=self.cfg, websocket=self.websocket)

        # Run Tasks
        return summary

