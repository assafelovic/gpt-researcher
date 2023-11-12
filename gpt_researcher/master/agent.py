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
        await self.stream_output("logs", self.agent)

        # Generate Sub-Queries
        sub_queries = await get_sub_queries(self.query, self.role, self.cfg)
        await self.stream_output("logs",
                                 f"🧠 I will conduct my research based on the following queries: {sub_queries}...")

        # Run Sub-Queries
        for sub_query in sub_queries:
            await self.stream_output("logs", f"🔎 Running research for '{sub_query}'...")
            context = await self.run_sub_query(sub_query)
            self.context.append(context)
            await self.stream_output("logs", context)

        # Conduct Research
        await self.stream_output("logs", f"✍️ Writing {self.report_type} for research task: {self.query}...")
        report = await generate_report(query=self.query, context=self.context,
                                       agent_role_prompt=self.role, report_type=self.report_type,
                                       websocket=self.websocket, cfg=self.cfg)
        time.sleep(1)
        return report

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
        urls = retriever.search()
        urls_to_scrape = []
        for url in urls:
            if url not in self.visited_urls:
                await self.stream_output("logs", f"✅ Adding source url to research: {url}\n")
                self.visited_urls.add(url)
                urls_to_scrape.append(url)

        # Scrape Urls
        await self.stream_output("logs", f"📝 Summarizing sources...")
        raw_data = scrape_urls(urls_to_scrape)
        # Summarize Raw Data
        summary = await summarize(query=sub_query, text=raw_data, agent_role_prompt=self.role, cfg=self.cfg)

        # Run Tasks
        return summary

    async def stream_output(self, type, output):
        """
        Streams output to the websocket
        Args:
            type:
            output:

        Returns:
            None
        """
        if not self.websocket:
            return print(output)
        await self.websocket.send_json({"type": type, "output": output})
