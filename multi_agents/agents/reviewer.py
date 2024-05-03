from datetime import datetime
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from .utils.views import print_agent_output

TEMPLATE = """You are an expert research report reviewer. \
You have been tasked with editing the following draft, which was written by a non-expert. \
Please accept the draft if it is good enough to publish, or send it for revision, along with your notes to guide the revision. \
Things you should be checking for:
- This draft MUST fully answer the original question
- This draft MUST be written in apa format
If not all of the above criteria are met, you should send appropriate revision notes.
"""

class ReviewerAgent:
    def __init__(self):
        pass

    def review_draft(self, draft: str):
        """
        Review a draft article
        :param draft:
        :return:
        """
        prompt = [{
            "role": "system",
            "content": TEMPLATE
        }, {
            "role": "user",
            "content": f"Draft: {draft}\n"
        }]

        lc_messages = convert_openai_messages(prompt)
        response = ChatOpenAI(model='gpt-4-turbo', max_retries=1).invoke(lc_messages).content
        return response

    def run(self, draft_state: dict):
        draft = draft_state.get("draft")
        task = draft_state.get("task")
        guidelines = task.get("guidelines")
        to_follow_guidelines = task.get("follow_guidelines")
        review = None
        if to_follow_guidelines:
            print_agent_output(f"Reviewing draft...", agent="REVIEWER")
            print_agent_output(f"Following guidelines {guidelines}...", agent="REVIEWER")
            review = self.review_draft(draft)
        else:
            print_agent_output(f"Ignoring guidelines...", agent="REVIEWER")
        return {"review": review}
