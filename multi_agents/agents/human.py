from .utils.views import print_agent_output
from .utils.llms import call_model

class HumanAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def review_plan(self, research_state: dict):
        print(f"HumanAgent websocket: {self.websocket}")
        print(f"HumanAgent stream_output: {self.stream_output}")
        layout = research_state.get("sections")

        user_feedback = None
        
        if self.websocket and self.stream_output:
            try:
                await self.stream_output("human_feedback", "request", f"Any feedback on this plan? {layout}? If not, please reply with 'no'.", self.websocket)
                response = await self.websocket.receive_text()
                print(f"Received response: {response}")  # Add this line for debugging
                user_feedback = response
            except Exception as e:
                print(f"Error receiving human feedback: {e}")
        else:
            user_feedback = input(f"Any feedback on this plan? {layout}? If not, please reply with 'no'.\n>> ")
        
        if user_feedback and user_feedback.lower() == "no":
            user_feedback = None

        return {"human_feedback": user_feedback}