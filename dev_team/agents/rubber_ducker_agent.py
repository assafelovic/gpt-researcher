from .utils.llms import call_model

class RubberDuckerAgent:
    async def think_aloud(self, state):
        prompt = f"""
        Based on the repository analysis:
        {state.get("repo_analysis")}
        
        And the web search results:
        {state.get("web_search_results")}
        
        Think out loud about the game plan for answering the user's question. 
        Explain your reasoning step by step.
        """

        response = await call_model(
            prompt=prompt,
            model=state.get("model"),
            response_format="json",
        )
        return {"rubber_ducker_thoughts": response} 