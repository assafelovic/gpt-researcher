from .utils.llms import call_model
sample_json = """
{
  "thoughts": "Your step-by-step reasoning here"
}
"""
class TechLeadAgent:
    async def review_and_compose(self, state):
        prompt = [
            {"role": "system", "content": f"""You are the Tech Lead responsible for replying directly to the developer who has a question: {state.get('query')}"""},
            {"role": "user", "content": f"""
                Please take into account the repository analysis:
                {state.get("repo_analysis")}
                
                The web search results:
                {state.get("web_search_results")}

                And your assistant's thoughts in how we should handle the query:
                {state.get("rubber_ducker_thoughts")}
                
                Your response to the developer should be clear, concise, and actionable.
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