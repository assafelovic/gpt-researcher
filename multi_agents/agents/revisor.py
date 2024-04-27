from datetime import datetime
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from .utils.views import print_agent_output

TEMPLATE =  """You are an expert writer.
You have been tasked by your editor with revising the following draft, which was written by a non-expert.
You may follow the editor's notes or not, as you see fit.
Draft:\n\n{draft}" + "Editor's notes:\n\n{notes}"""

class RevisorAgent:
    def __init__(self):
        pass

    def revise_draft(self, draft: str):
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
        response = ChatOpenAI(model='gpt-4-0125-preview', max_retries=1).invoke(lc_messages).content
        return response

    def run(self, draft: str):
        print_agent_output(f"Rewriting draft based on feedback...", agent="REVISOR")
        review = self.revise_draft(draft)
        return review