from datetime import datetime
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
import json

EDITOR_TEMPLATE = """You are an editor. \
You have been tasked with editing the following draft, which was written by a non-expert. \
Please accept the draft if it is good enough to publish, or send it for revision, along with your notes to guide the revision. \
Things you should be checking for:
- This draft MUST fully answer the original question
- This draft MUST be written in apa format
If not all of the above criteria are met, you should send appropriate revision notes.
"""


class EditorAgent:
    def __init__(self, task: dict):
        self.max_sub_headers = task.get("max_sub_headers")

    def create_outline(self, summary_report: str):
        """
        Curate relevant sources for a query
        :param summary_report:
        :return:
        :param total_sub_headers:
        :return:
        """
        prompt = [{
            "role": "system",
            "content": "You are a research director. Your goal is to oversee the research project"
                       " from inception to completion.\n "
        }, {
            "role": "user",
            "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                       f"Research summary report: '{summary_report}'\n\n"
                       f"Your task is to generate an outline for the research project"
                       f" based on the research summary report above.\n"
                       f"You must return nothing but a JSON with the fields 'title' (str) and "
                       f"'subheaders' (maximum {self.max_sub_headers} subheaders strings) with the following structure: "
                       f"'{{title: string research title, "
                       f"subheaders: ['sub header1', 'sub header2','sub header3', ...]}}.\n "
        }]

        lc_messages = convert_openai_messages(prompt)
        optional_params = {
            "response_format": {"type": "json_object"}
        }
        response = ChatOpenAI(model='gpt-4-turbo', max_retries=1, model_kwargs=optional_params).invoke(lc_messages).content
        return json.loads(response)

    def run(self, summary_report: str):
        research_info = self.create_outline(summary_report)
        return research_info
