from gpt_researcher import GPTResearcher
from colorama import Fore, Style
from .utils.views import print_agent_output


class ResearchAgent:
    def __init__(self):
        pass

    async def research(self, query: str, research_report: str = "research_report", parent_query: str = ""):
        # Initialize the researcher
        researcher = GPTResearcher(parent_query=parent_query, query=query, report_type=research_report, config_path=None)
        # Conduct research on the given query
        await researcher.conduct_research()
        # Write the report
        report = await researcher.write_report()

        return report

    async def run_subtopic_research(self, title: str, subtopic: str):
        try:
            report = await self.research(parent_query=title, query=subtopic, research_report="subtopic_report")
        except Exception as e:
            print(f"{Fore.RED}Error in researching topic {subtopic}: {e}{Style.RESET_ALL}")
            report = None
        return {subtopic: report}

    async def run_initial_research(self, research_state: dict):
        task = research_state.get("task")
        query = task.get("query")
        print_agent_output(f"Running initial research on the following query: {query}", agent="RESEARCHER")
        return {"task": task, "initial_research": await self.research(query)}

    async def run_depth_research(self, draft_state: dict):
        title = draft_state.get("title")
        topic = draft_state.get("topic")
        print_agent_output(f"Running in depth research on the following report topic: {topic}", agent="RESEARCHER")
        research_draft = await self.run_subtopic_research(title, topic)
        return {"draft": research_draft}
