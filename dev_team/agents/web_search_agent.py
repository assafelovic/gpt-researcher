from gpt_researcher import GPTResearcher

class WebSearchAgent:
    def __init__(self, repo_name=None):
        self.repo_name = repo_name

    async def search_web(self, state):
        query = state['query'] if isinstance(state, dict) else state
        
        if self.repo_name:
            query += f" - the repo_name is: {self.repo_name}"
            
        researcher = GPTResearcher(
            query=query + " - the repo_name is: " + self.repo_name,
            report_type="research_report",
            report_source="web"
        )
        await researcher.conduct_research()
        report = await researcher.write_report()
        return report