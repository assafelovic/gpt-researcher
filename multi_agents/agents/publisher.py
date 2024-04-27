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

    async def publish_research_report(self, research_report_data: dict):
        subheaders = '\n\n'.join(f"{value}"
                                 for subheader in research_report_data.get("subheaders")
                                 for key, value in subheader.items())
        references = '\n'.join(f"{reference}" for reference in research_report_data.get("sources"))
        layout = f"""#{research_report_data.get('title')}
## Introduction
{research_report_data.get('introduction')}

{subheaders}

## Conclusion
{research_report_data.get('conclusion')}

## References
{references}
"""
        publish_formats = self.task.get("publish_formats")
        await self.write_report_to_formats(layout, publish_formats)
        return layout

    async def write_report_to_formats(self, layout:str, publish_formats: dict):
        if publish_formats.get("pdf"):
            await write_md_to_pdf(layout, self.output_dir)
        if publish_formats.get("docx"):
            await write_md_to_word(layout, self.output_dir)
        if publish_formats.get("markdown"):
            await write_text_to_md(layout, self.output_dir)

    async def run(self, research_report_data: dict):
        print_agent_output(output="Publishing final research report...", agent="PUBLISHER")
        final_research_report = await self.publish_research_report(research_report_data)
        return final_research_report
