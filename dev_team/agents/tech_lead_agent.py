from .utils.llms import call_model
from dev_team.agents import GithubAgent
import os
sample_json = """
{
  "thoughts": "Your step-by-step reasoning here"
}
"""
class TechLeadAgent:
    async def review_and_compose(self, state):
        github_agent = GithubAgent(github_token=os.environ.get("GITHUB_TOKEN"), repo_name='elishakay/gpt-researcher', branch_name="devs", vector_store=state.get("vector_store"))

        file_names_to_search = ["backend/server.py", "backend/websocket_manager.py"]

        # Fetch the matching documents
        matching_docs = await github_agent.search_by_file_name(file_names_to_search)
        print("matching_docs: ", matching_docs,flush=True)

        prompt = [
            {"role": "system", "content": f"""You are the Tech Lead responsible for replying directly to the developer who has a question: {state.get('query')}"""},
            {"role": "user", "content": f"""
                Please take into account the repository analysis:
                {state.get("repo_analysis")}
                
                The web search results:
                {state.get("web_search_results")}

                And your assistant's thoughts in how we should handle the query:
                {state.get("rubber_ducker_thoughts")}

                Here is the repo's directory structure: {state.get("github_data")}

                Here are some relevant files from the developer's branch: {matching_docs}
                
                If neccessary, please provide the full code snippets 
                & relevant file names to add or edit on the branch in order to solve the developer's question.
                
                Pretend that I am the developer.
                Be cool & friendly.

                You MUST return nothing but a JSON in the following format (without json markdown).
                Respond in the following JSON format: {sample_json}
            """
            }
        ]
        
        response = await call_model(
            prompt=prompt,
            model=state.get("model")
        )
        return {"tech_lead_review": response}