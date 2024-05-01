from datetime import datetime
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
import json5 as json
from .utils.views import print_agent_output

sample_json = """
{
  "title": research title as given in input,
  "date": today's date,
  "table_of_contents": A table of contents in markdown syntax based on the research headers and subheaders,
  "introduction": An indepth introduction to the topic in markdown syntax and hyperlink references to relevant sources,
  "conclusion": A conclusion to the entire research based on all research data in markdown syntax and hyperlink references to relevant sources,
  "sources": A list of all sources in the entire research data in markdown syntax and apa format
}
"""


class WriterAgent:
    def __init__(self):
        pass

    def write(self, research_data: dict):
        query = research_data.get("title")
        data = research_data.get("research_data")

        prompt = [{
            "role": "system",
            "content": "You are a research writer. Your sole purpose is to write a well-written "
                       "research reports about a "
                       "topic based on research findings and information.\n "
        }, {
            "role": "user",
            "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                       f"Query or Topic: {query}\n"
                       f"Research data: {str(data)}\n"
                       f"Your task is to write a critically acclaimed in depth and long "
                       f"introduction and conclusion in markdown syntax "
                       f"based on the provided research data.\n"
                       f"Please include any relevant sources to the introduction and conclusion as markdown hyperlinks -"
                       f"For example: 'This is a sample text. ([url website](url))'\n"
                       f"You MUST return nothing but a JSON in the following format:\n"
                       f"{sample_json}\n\n"

        }]

        lc_messages = convert_openai_messages(prompt)
        optional_params = {
            "response_format": {"type": "json_object"}
        }

        response = ChatOpenAI(model='gpt-4-turbo', max_retries=1, model_kwargs=optional_params).invoke(lc_messages).content
        return json.loads(response)

    def run(self, research_data: dict):
        print_agent_output(f"Writing final research report based on research data...", agent="WRITER")
        research_report_json = self.write(research_data)
        research_report_json["subheaders"] = research_data.get("research_data")
        #print(json.dumps(research_report_json, indent=4))
        return research_report_json
