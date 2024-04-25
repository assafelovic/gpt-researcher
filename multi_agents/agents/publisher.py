import os
from .utils.file_utils import write_md_to_pdf, write_md_to_word


class PublisherAgent:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    async def publish_research_report(self, research_report_data: dict):
        subheaders = '\n\n'.join(f"{value}"
                                 for subheader in research_report_data.get("subheaders")
                                 for key, value in subheader.items())
        references = '\n'.join(f"* {reference}" for reference in research_report_data.get("sources"))
        layout = f"""#{research_report_data.get('title')}
## Introduction
{research_report_data.get('introduction')}

{subheaders}

## Conclusion
{research_report_data.get('conclusion')}

## References
{references}
"""
        await write_md_to_word(layout, self.output_dir)
        await write_md_to_pdf(layout, self.output_dir)
        return layout

    async def run(self, research_report_data: dict):
        final_research_report = await self.publish_research_report(research_report_data)
        return final_research_report
