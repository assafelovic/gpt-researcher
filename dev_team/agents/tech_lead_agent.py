from .utils.llms import call_model

class TechLeadAgent:
    async def review_and_compose(self, rubber_ducker_output):
        prompt = f"""
        Review the following plan:
        {rubber_ducker_output}
        
        Analyze whether it's a good plan or not. Then, compose a response to the user 
        based on this plan and the previous steps' outputs. The response should be 
        clear, concise, and actionable.
        """
        
        response = await call_model("gpt-4", prompt)
        return response