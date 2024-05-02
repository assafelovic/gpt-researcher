from datetime import datetime
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from .utils.views import print_agent_output
import json


class EditorAgent:
    def __init__(self, task: dict):
        self.max_sections = task.get("max_sections")

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
                       f"Your task is to generate an outline of sections headers for the research project"
                       f" based on the research summary report above.\n"
                       f"You must generate a maximum of {self.max_sections} section headers.\n"
                       f"You must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\n"
                       f"You must return nothing but a JSON with the fields 'title' (str) and "
                       f"'sections' (maximum {self.max_sections} section headers) with the following structure: "
                       f"'{{title: string research title, date: today's date, "
                       f"sections: ['section header 1', 'section header 2', 'section header 3' ...]}}.\n "
        }]

        lc_messages = convert_openai_messages(prompt)
        optional_params = {
            "response_format": {"type": "json_object"}
        }
        response = ChatOpenAI(model='gpt-4-turbo', max_retries=1, model_kwargs=optional_params).invoke(lc_messages).content
        return json.loads(response)

    def run(self, research_state: dict):
        initial_research = research_state.get("initial_research")
        print_agent_output(f"Editor: Planning an outline layout based on initial research...", agent="EDITOR")
        research_info = self.create_outline(initial_research)
        return {
            "title": research_info.get("title"),
            "date": research_info.get("date"),
            "sections": research_info.get("sections")
        }
