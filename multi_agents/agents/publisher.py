from .utils.file_formats import \
    write_md_to_pdf, \
    write_md_to_word, \
    write_text_to_md

from .utils.views import print_agent_output


class PublisherAgent:
    def __init__(self, output_dir: str, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.output_dir = output_dir
        self.headers = headers or {}
        
    async def publish_research_report(self, research_state: dict, publish_formats: dict):
        layout = self.generate_layout(research_state)
        await self.write_report_by_formats(layout, publish_formats)

        return layout

    def generate_layout(self, research_state: dict):
        # Add safety checks for research_data
        research_data = research_state.get("research_data", [])
        if research_data is None:
            research_data = []
            
        # Create sections with proper error handling
        sections = ""
        try:
            sections = '\n\n'.join(f"{value}"
                                 for subheader in research_data
                                 for key, value in subheader.items())
        except Exception as e:
            print(f"Error generating sections: {e}")
            sections = ""
            
        # Add safety checks for sources
        sources = research_state.get("sources", [])
        if sources is None:
            sources = []
            
        # Create references with proper error handling
        references = ""
        try:
            references = '\n'.join(f"{reference}" for reference in sources)
        except Exception as e:
            print(f"Error generating references: {e}")
            references = ""
            
        # Get headers with default values
        headers = research_state.get("headers", {})
        if headers is None:
            headers = {}
            
        # Default values for all required fields
        title = headers.get("title", research_state.get("title", "Research Report"))
        date_header = headers.get("date", "Date")
        date_value = research_state.get("date", "")
        intro_header = headers.get("introduction", "Introduction")
        intro_value = research_state.get("introduction", "")
        toc_header = headers.get("table_of_contents", "Table of Contents")
        toc_value = research_state.get("table_of_contents", "")
        conclusion_header = headers.get("conclusion", "Conclusion")
        conclusion_value = research_state.get("conclusion", "")
        references_header = headers.get("references", "References")
        
        layout = f"""# {title}
#### {date_header}: {date_value}

## {intro_header}
{intro_value}

## {toc_header}
{toc_value}

{sections}

## {conclusion_header}
{conclusion_value}

## {references_header}
{references}
"""
        return layout

    async def write_report_by_formats(self, layout:str, publish_formats: dict):
        if publish_formats.get("pdf"):
            await write_md_to_pdf(layout, self.output_dir)
        if publish_formats.get("docx"):
            await write_md_to_word(layout, self.output_dir)
        if publish_formats.get("markdown"):
            await write_text_to_md(layout, self.output_dir)

    async def run(self, research_state: dict):
        task = research_state.get("task")
        publish_formats = task.get("publish_formats")
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "publishing", f"Publishing final research report based on retrieved data...", self.websocket)
        else:
            print_agent_output(output="Publishing final research report based on retrieved data...", agent="PUBLISHER")
        final_research_report = await self.publish_research_report(research_state, publish_formats)
        return {"report": final_research_report}
