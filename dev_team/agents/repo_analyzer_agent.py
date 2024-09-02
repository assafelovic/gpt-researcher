from gpt_researcher import GPTResearcher

class RepoAnalyzerAgent:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def analyze_repo(self, query):
        researcher = GPTResearcher(
            query=query,
            report_type="research_report",
            report_source="langchain_vectorstore",
            vector_store=self.vector_store,
        )
        await researcher.conduct_research()
        report = await researcher.write_report()
        return report