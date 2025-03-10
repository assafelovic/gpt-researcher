from datetime import datetime
import json5 as json
from .utils.views import print_agent_output
from .utils.llms import call_model

sample_json = """
{
  "table_of_contents": A table of contents in markdown syntax (using '-') based on the research headers and subheaders,
  "introduction": An indepth introduction to the topic in markdown syntax and hyperlink references to relevant sources,
  "sections": An array of section objects, each with a "title" and "content" field. The content should be in markdown syntax with hyperlink references to relevant sources,
  "conclusion": A conclusion to the entire research based on all research data in markdown syntax and hyperlink references to relevant sources,
  "sources": A list with strings of all used source links in the entire research data in markdown syntax and apa citation format. For example: ['-  Title, year, Author [source url](source)', ...]
}
"""


class WriterAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers

    def get_headers(self, research_state: dict):
        return {
            "title": research_state.get("title"),
            "date": "Date",
            "introduction": "Introduction",
            "table_of_contents": "Table of Contents",
            "conclusion": "Conclusion",
            "references": "References",
        }

    async def write_sections(self, research_state: dict):
        query = research_state.get("title")
        data = research_state.get("research_data")
        task = research_state.get("task", {})
        follow_guidelines = task.get("follow_guidelines", False)
        guidelines = task.get("guidelines", "")
        # Get model from task or use a default model if None
        model = task.get("model")
        if model is None:
            from gpt_researcher.config.config import Config
            cfg = Config()
            model = cfg.smart_llm_model  # Use the default smart model from config

        # Check if this is deep research data (has a single entry with 'topic' and 'content')
        is_deep_research = False
        if data and len(data) == 1 and 'topic' in data[0] and 'content' in data[0]:
            is_deep_research = True
            
        prompt = [
            {
                "role": "system",
                "content": "You are a research writer. Your sole purpose is to write a well-written "
                "research report about a "
                "topic based on research findings and information.\n ",
            },
            {
                "role": "user",
                "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                f"Query or Topic: {query}\n"
                f"Research data: {str(data)}\n"
                f"Your task is to write an in-depth, well-written and detailed research report based on the provided research data. "
                f"This should include an introduction, main content sections with appropriate headers, and a conclusion. "
                f"Do not include headers in the introduction or conclusion results.\n"
                f"{'For deep research data, analyze the content and organize it into logical sections with appropriate headers.' if is_deep_research else ''}\n"
                f"You MUST include any relevant sources to all sections as markdown hyperlinks -"
                f"For example: 'This is a sample text. ([url website](url))'\n\n"
                f"{f'You must follow the guidelines provided: {guidelines}' if follow_guidelines else ''}\n"
                f"You MUST return nothing but a JSON in the following format (without json markdown):\n"
                f"{sample_json}\n\n",
            },
        ]

        response = await call_model(
            prompt,
            model,
            response_format="json",
        )
        return response

    async def revise_headers(self, task: dict, headers: dict):
        # Get model from task or use a default model if None
        model = task.get("model")
        if model is None:
            from gpt_researcher.config.config import Config
            cfg = Config()
            model = cfg.smart_llm_model  # Use the default smart model from config
            
        prompt = [
            {
                "role": "system",
                "content": """You are a research writer. 
Your sole purpose is to revise the headers data based on the given guidelines.""",
            },
            {
                "role": "user",
                "content": f"""Your task is to revise the given headers JSON based on the guidelines given.
You are to follow the guidelines but the values should be in simple strings, ignoring all markdown syntax.
You must return nothing but a JSON in the same format as given in headers data.
Guidelines: {task.get("guidelines")}\n
Headers Data: {headers}\n
""",
            },
        ]

        response = await call_model(
            prompt,
            model,
            response_format="json",
        )
        return {"headers": response}

    async def run(self, research_state: dict):
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "writing_report",
                f"Writing final research report based on research data...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Writing final research report based on research data...",
                agent="WRITER",
            )

        research_layout_content = await self.write_sections(research_state)
        
        # If research_layout_content is None, create a default empty structure
        if research_layout_content is None:
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "error",
                    "Error generating research layout content. Using default empty structure.",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Error generating research layout content. Using default empty structure.",
                    agent="WRITER",
                )
            research_layout_content = {
                "table_of_contents": "",
                "introduction": "",
                "sections": [],
                "conclusion": "",
                "sources": []
            }

        if research_state.get("task", {}).get("verbose"):
            if self.websocket and self.stream_output:
                research_layout_content_str = json.dumps(
                    research_layout_content, indent=2
                )
                await self.stream_output(
                    "logs",
                    "research_layout_content",
                    research_layout_content_str,
                    self.websocket,
                )
            else:
                print_agent_output(research_layout_content, agent="WRITER")

        headers = self.get_headers(research_state)
        if research_state.get("task", {}).get("follow_guidelines"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "rewriting_layout",
                    "Rewriting layout based on guidelines...",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Rewriting layout based on guidelines...", agent="WRITER"
                )
            headers_response = await self.revise_headers(
                task=research_state.get("task", {}), headers=headers
            )
            if headers_response and "headers" in headers_response:
                headers = headers_response.get("headers")

        return {**research_layout_content, "headers": headers}
