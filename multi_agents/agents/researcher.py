from gpt_researcher import GPTResearcher
import asyncio
from colorama import Fore, Style
from .utils.views import print_agent_output
import json


class ResearchAgent:
    def __init__(self):
        pass

    async def research(self, query: str, research_report: str = "research_report", parent_query: str = ""):
        # Initialize the researcher
        researcher = GPTResearcher(query=query, report_type=research_report, config_path=None, parent_query=parent_query)
        # Conduct research on the given query
        await researcher.conduct_research()
        # Write the report
        report = await researcher.write_report()

        return report

    async def run_subtopic_research(self, title: str, subtopic: str):
        try:
            report = await self.research(f"{subtopic}", research_report="subtopic_report", parent_query=title)
        except Exception as e:
            print(f"{Fore.RED}Error in researching topic {subtopic}: {e}{Style.RESET_ALL}")
            report = None
        return {subtopic: report}

    async def run_initial_research(self, task: dict):
        query = task.get("query")
        print_agent_output(f"Running initial research on the following query: {query}", agent="RESEARCHER")
        return await self.research(query)

    async def run_depth_research(self, outline: dict):
        title = outline.get("title")
        subheaders = outline.get("subheaders")
        print_agent_output(f"Running in depth research on the following subtopics: {subheaders}", agent="RESEARCHER")

        tasks = [self.run_subtopic_research(title, query) for query in subheaders]
        results = await asyncio.gather(*tasks)
        return {"title": title, "research_data": results}
