"""A detailed report's cost must include the subtopic researchers.

Each subtopic runs its own ``GPTResearcher``, and the server and REST API
report ``DetailedReport.gpt_researcher.get_costs()``. Without rolling the
subtopic costs into the main researcher, a measured detailed report that cost
$0.28 reported $0.06.
"""

import pytest

from gpt_researcher import GPTResearcher
from gpt_researcher.actions.markdown_processing import extract_headers, extract_sections
import backend.report_type.detailed_report.detailed_report as detailed_report


class _SubtopicAssistant:
    def __init__(self, cost):
        self._cost = cost
        self.visited_urls = {"https://example.com/subtopic"}

    def get_costs(self):
        return self._cost

    async def get_similar_written_contents_by_draft_section_titles(self, *args, **kwargs):
        return []

    async def write_report(self, **kwargs):
        return "## Subtopic\n\nBody."


def _detailed_report_with_main_researcher():
    report = detailed_report.DetailedReport.__new__(detailed_report.DetailedReport)
    main = GPTResearcher.__new__(GPTResearcher)
    main.research_costs = 0.05
    main.step_costs = {"research": 0.05}
    main._current_step = "report_writing"
    main.log_handler = None
    main.extract_headers = extract_headers
    main.extract_sections = extract_sections
    report.gpt_researcher = main
    report.global_written_sections = []
    report.global_urls = set()
    report.existing_headers = []
    return report


async def test_subtopic_costs_roll_up_into_the_report_total():
    report = _detailed_report_with_main_researcher()

    await report._write_subtopic_report({"task": "A"}, _SubtopicAssistant(0.07), [])
    await report._write_subtopic_report({"task": "B"}, _SubtopicAssistant(0.08), [])

    assert report.gpt_researcher.get_costs() == pytest.approx(0.20)
    assert "https://example.com/subtopic" in report.global_urls
