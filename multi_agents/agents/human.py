from .utils.views import print_agent_output
from .utils.llms import call_model

class HumanAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def review_plan(self, research_state: dict):
        layout = research_state.get("sections")
        if self.websocket and self.stream_output:
            await self.stream_output("human_feedback", "request", f"Any feedback on this plan? {layout}? If not, please reply with 'no'.", self.websocket)
            response = await self.websocket.receive_text()
            user_feedback = response if response.lower() != "no" else None
        else:
            user_feedback = None
        return {"human_feedback": user_feedback}