from .utils.file_formats import write_md_to_pdf, write_md_to_word, write_text_to_md
import os
import aiofiles

from .utils.views import print_agent_output

class PublisherAgent:
    def __init__(self, output_dir: str, websocket=None, stream_output=None, headers=None, output_file: str = None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.output_dir = output_dir.strip()
        self.headers = headers or {}
        self.output_file = output_file

    async def publish_research_report(self, research_state: dict, publish_formats: dict):
        layout = self.generate_layout(research_state)
        await self.write_report_by_formats(layout, publish_formats)
        return layout

    def generate_layout(self, research_state: dict):
        sections = []
        for subheader in research_state.get("research_data", []):
            if isinstance(subheader, dict):
                for key, value in subheader.items():
                    sections.append(f"{value}")
            else:
                sections.append(f"{subheader}")

        sections_text = '\n\n'.join(sections)
        references = '\n'.join(f"{reference}" for reference in research_state.get("sources", []))
        headers = research_state.get("headers", {})
        layout = f"""# {headers.get('title')}
#### {headers.get("date")}: {research_state.get('date')}

## {headers.get("introduction")}
{research_state.get('introduction')}

## {headers.get("table_of_contents")}
{research_state.get('table_of_contents')}

{sections_text}

## {headers.get("conclusion")}
{research_state.get('conclusion')}

## {headers.get("references")}
{references}
"""
        return layout

    async def write_report_by_formats(self, layout: str, publish_formats: dict):
        if self.output_file:
            # Create output folder if it does not exist
            output_folder = os.path.dirname(self.output_file)
            os.makedirs(output_folder, exist_ok=True)
            ext = os.path.splitext(self.output_file)[1].lower()
            if ext == ".md":
                async with aiofiles.open(self.output_file, "w", encoding="utf-8") as f:
                    await f.write(layout)
            elif ext == ".pdf":
                await write_md_to_pdf(layout, os.path.dirname(self.output_file))
            elif ext == ".docx":
                await write_md_to_word(layout, os.path.dirname(self.output_file))
            return
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
            await self.stream_output(
                "logs",
                "publishing",
                "Publishing final research report based on retrieved data...",
                self.websocket,
            )
        else:
            print_agent_output(output="Publishing final research report based on retrieved data...", agent="PUBLISHER")
        final_research_report = await self.publish_research_report(research_state, publish_formats)
        return {"report": final_research_report}
