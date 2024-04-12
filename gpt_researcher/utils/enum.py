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


def get_prompt_by_report_type(report_type):
    report_type_mapping = {
        ReportType.ResearchReport.value: generate_report_prompt,
        ReportType.ResourceReport.value: generate_resource_report_prompt,
        ReportType.OutlineReport.value: generate_outline_report_prompt,
        ReportType.CustomReport.value: generate_custom_report_prompt,
        ReportType.SubtopicReport.value: generate_subtopic_report_prompt
    }
    return report_type_mapping[report_type]