import os
from .utils.file_formats import \
    write_md_to_pdf, \
    write_md_to_word, \
    write_text_to_md

from .utils.views import print_agent_output


class PublisherAgent:
    def __init__(self, output_dir: str, task: dict):
        self.output_dir = output_dir
        self.task = task

    async def publish_research_report(self, research_data: dict):
        layout = self.generate_layout(research_data)
        await self.write_report_by_formats(layout, self.task.get("publish_formats"))

        return layout

    def generate_layout(self, research_report_data: dict):
        subheaders = '\n\n'.join(f"{value}"
                                 for subheader in research_report_data.get("subheaders")
                                 for key, value in subheader.items())
        references = '\n'.join(f"{reference}" for reference in research_report_data.get("sources"))
        layout = f"""#{research_report_data.get('title')}
#### Date: {research_report_data.get('date')}

## Introduction
{research_report_data.get('introduction')}

## Table of Contents
{research_report_data.get('table_of_contents')}

{subheaders}

## Conclusion
{research_report_data.get('conclusion')}

## References
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

    async def run(self, research_data: dict):
        print_agent_output(output="Publishing final research report based on retrieved data...", agent="PUBLISHER")
        final_research_report = await self.publish_research_report(research_data)
        return final_research_report
