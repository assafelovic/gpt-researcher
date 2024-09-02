from gpt_researcher import GPTResearcher

class WebSearchAgent:
    async def search_web(self, query):
        researcher = GPTResearcher(
            query=query,
            report_type="research_report",
            report_source="web"
        )
        await researcher.conduct_research()
        report = await researcher.write_report()
        return report