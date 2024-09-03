from .utils.llms import call_model

class RubberDuckerAgent:
    async def think_aloud(self, repo_analysis, web_search):
        prompt = f"""
        Based on the repository analysis:
        {repo_analysis}
        
        And the web search results:
        {web_search}
        
        Think out loud about the game plan for answering the user's question. 
        Explain your reasoning step by step.
        """
        
        response = await call_model("gpt-4", prompt)
        return {"rubber_ducker_output": response} 