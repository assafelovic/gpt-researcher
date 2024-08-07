from .utils.views import print_agent_output
from .utils.llms import call_model

class HumanAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def review_plan(self, research_state: dict):
        """
        Review a draft article
        :param draft_state:
        :return:
        """
        layout = research_state.get("sections")
        user_feedback = input(f"Any feedback on this plan? {layout}? If not, please reply with 'no'.\n>> ")
        if "no" in user_feedback:
            user_feedback = None
        return {"human_feedback": user_feedback}
