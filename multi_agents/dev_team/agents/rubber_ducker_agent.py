from .utils.llms import call_model
from multi_agents.dev_team.agents import GithubAgent
import os
sample_json = """
{
  "thoughts": "Your step-by-step reasoning here"
}
"""

class RubberDuckerAgent:
    async def think_aloud(self, state):
        github_agent = GithubAgent(github_token=os.environ.get("GITHUB_TOKEN"), repo_name=state.get("repo_name"), branch_name=state.get("branch_name"), vector_store=state.get("vector_store"))

        file_names_to_search = state.get("relevant_file_names")

        # Fetch the matching documents
        matching_docs = await github_agent.search_by_file_name(file_names_to_search)
        # print("matching_docs: ", matching_docs,flush=True)

        prompt = [
            {"role": "system", "content": "You are a rubber duck debugging assistant."},
            {"role": "user", "content": f"""
             
            Here is the developer's question: {state.get('query')}

            Here is the repo's directory structure: {state.get("github_data")}

            Here are some relevant files from the developer's branch: {matching_docs}
                
            If neccessary, please provide the full code snippets 
            & relevant file names to add or edit on the branch in order to solve the developer's question.
            
            Think out loud about the game plan for answering the user's question. 
            Explain your reasoning step by step.

            If it sounds like the user is asking for a feature, or a bug fix, please provide the relevant file names to edit with the relevant code to edit or add within those files.

            You MUST return nothing but a JSON in the following format.
            Respond in the following JSON format: {sample_json}
            Also, please make sure you DO NOT include any backticks in your response - it MUST be a VALID JSON.
            """}
        ]

        response = await call_model(
            prompt=prompt,
            model=state.get("model")
        )
        return {"rubber_ducker_thoughts": response} 