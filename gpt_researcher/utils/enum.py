from enum import Enum
from gpt_researcher.master.prompts import \
    generate_report_prompt, \
    generate_resource_report_prompt, \
    generate_outline_report_prompt, \
    generate_custom_report_prompt, \
    generate_subtopic_report_prompt

class ReportType(Enum):
    ResearchReport = 'research_report'
    ResourceReport = 'resource_report'
    OutlineReport = 'outline_report'
    CustomReport = 'custom_report'
    DetailedReport = 'detailed_report'
    SubtopicReport = 'subtopic_report'

report_type_mapping = {
    ReportType.ResearchReport.value: generate_report_prompt,
    ReportType.ResourceReport.value: generate_resource_report_prompt,
    ReportType.OutlineReport.value: generate_outline_report_prompt,
    ReportType.CustomReport.value: generate_custom_report_prompt,
    ReportType.SubtopicReport.value: generate_subtopic_report_prompt
}


def get_prompt_by_report_type(report_type):
    default_report_type = ReportType.ResearchReport.value
    prompt_by_type = report_type_mapping.get(report_type)
    if not prompt_by_type:
        prompt_by_type = report_type_mapping.get(default_report_type)
        print(f"Invalid report type: {report_type}. Using default report type: {default_report_type}")
    return prompt_by_type
