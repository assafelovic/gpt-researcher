from gpt_researcher import GPTResearcher

class RepoAnalyzerAgent:
    def __init__(self):
        self.vector_store = None

    async def analyze_repo(self, state):
        query = state.get("query")
        vector_store = state.get("vector_store")
        print('state', state)
        print("Analyzing repo vector store", vector_store)

        researcher = GPTResearcher(
            query=query,
            report_type="research_report",
            report_source="langchain_vectorstore",
            vector_store=vector_store,
        )
        await researcher.conduct_research()
        report = await researcher.write_report()
        return {"repo_analysis": report}