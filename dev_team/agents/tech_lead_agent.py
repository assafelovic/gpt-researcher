from .utils.llms import call_model

class TechLeadAgent:
    async def review_and_compose(self, state):
        prompt = f"""
        Review the following plan:
        {state.get("rubber_ducker_thoughts")}
        
        Analyze whether it's a good plan or not. Then, compose a response to the user 
        based on this plan and the previous steps' outputs. The response should be 
        clear, concise, and actionable.

        Please also take into account the repository analysis:
        {state.get("repo_analysis")}
        
        And the web search results:
        {state.get("web_search_results")}
        """
        
        response = await call_model(
            prompt=prompt,
            model=state.get("model"),
            response_format="json",
        )
        return {"tech_lead_review": response}