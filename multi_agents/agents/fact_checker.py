from .utils.views import print_agent_output
from .utils.llms import call_model

class FactCheckerAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def check_facts(self, research_state: dict):
        task = research_state.get("task")
        
        # Assemble a draft representation for the fact checker
        intro = research_state.get("introduction", "")
        conclusion = research_state.get("conclusion", "")
        data = research_state.get("research_data", [])
        
        draft = f"Introduction:\n{intro}\n\nSections Data:\n{data}\n\nConclusion:\n{conclusion}"

        prompt = [
            {
                "role": "system",
                "content": "You are a diligent Fact Checker Agent. Your goal is to review a research report draft, identify potential factual inaccuracies, hallucinations, or inconsistencies based on the provided research context, and decide if it needs to be sent back to the writer for revision.",
            },
            {
                "role": "user",
                "content": f"Review the following draft for factual accuracy:\n\n{draft}\n\nIf you find critical errors, provide a list of them so the writer can revise the draft. If the draft is factually sound, return exactly the string 'None'. Do not return any other text if it is accepted."
            }
        ]

        response = await call_model(prompt, model=task.get("model"))
        return response

    async def run(self, research_state: dict):
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "fact_checking",
                f"Checking facts in the assembled draft...",
                self.websocket,
            )
        else:
            print_agent_output(f"Checking facts in the assembled draft...", agent="FACT_CHECKER")

        review = await self.check_facts(research_state)

        if "None" in review:
            review = None
            if self.websocket and self.stream_output:
                await self.stream_output("logs", "fact_checking", "Draft accepted by Fact Checker.", self.websocket)
            else:
                print_agent_output("Draft accepted by Fact Checker.", agent="FACT_CHECKER")
        else:
            if self.websocket and self.stream_output:
                await self.stream_output("logs", "fact_checking", f"Fact Checker found issues: {review}...", self.websocket)
            else:
                print_agent_output(f"Fact Checker found issues: {review}...", agent="FACT_CHECKER")

        return {"fact_check_notes": review}
