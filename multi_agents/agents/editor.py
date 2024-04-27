from datetime import datetime
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from .utils.views import print_agent_output
import json


class EditorAgent:
    def __init__(self, task: dict):
        self.max_subheaders = task.get("max_subheaders")

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
                       f"Your task is to generate an outline of subheaders for the research project"
                       f" based on the research summary report above.\n"
                       f"You must generate a maximum of {self.max_subheaders} subheaders.\n"
                       f"You must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\n"
                       f"You must return nothing but a JSON with the fields 'title' (str) and "
                       f"'subheaders' (maximum {self.max_subheaders} subheaders) with the following structure: "
                       f"'{{title: string research title, "
                       f"subheaders: ['subheader1', 'subheader2', 'subheader3' ...]}}.\n "
        }]

        lc_messages = convert_openai_messages(prompt)
        optional_params = {
            "response_format": {"type": "json_object"}
        }
        response = ChatOpenAI(model='gpt-4-turbo', max_retries=1, model_kwargs=optional_params).invoke(lc_messages).content
        return json.loads(response)

    def run(self, summary_report: str):
        print_agent_output(f"Editor: Planning an outline layout based on initial research...", agent="EDITOR")
        research_info = self.create_outline(summary_report)
        return research_info
