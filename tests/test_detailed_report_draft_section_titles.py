"""A detailed report must keep the draft section titles it asked the model for.

``generate_draft_section_titles()`` returns the model's markdown split into lines
(``List[str]``), and ``GPTResearcher.get_draft_section_titles()`` is documented as
returning ``list[str]``. ``DetailedReport._research_subtopic`` used to stringify
that list, so ``extract_headers()`` saw ``"['### A', '### B']"`` -- one plain
paragraph -- and produced no headings. The draft titles then never reached the
"do not repeat these sections" guidance or the per-title written-content lookup.
"""

from types import SimpleNamespace

from gpt_researcher.actions.markdown_processing import extract_headers
import backend.report_type.detailed_report.detailed_report as detailed_report

DRAFT_TITLES = ["### Battery chemistry", "### Charging networks"]


class _StubResearcher:
    """Stands in for the subtopic GPTResearcher built by _research_subtopic."""

    def __init__(self, **kwargs):
        self.query = kwargs.get("query")
        self.context = []
        self.visited_urls = set()
        self.cfg = SimpleNamespace(max_search_results_per_query=5)
        self.mcp_configs = None
        self.mcp_strategy = None
        self.agent = "Research agent"
        self.role = "Research role"

    async def conduct_research(self):
        return "offline context"

    async def get_draft_section_titles(self, current_subtopic):
        return list(DRAFT_TITLES)


def _bare_detailed_report():
    report = detailed_report.DetailedReport.__new__(detailed_report.DetailedReport)
    report.query = "battery chemistries"
    report.tone = None
    report.report_source = "web"
    report.query_domains = []
    report.headers = {}
    report.subtopics = []
    report.websocket = None
    report.source_urls = []
    report.document_urls = []
    report.config_path = None
    report.complement_source_urls = False
    report.max_search_results = None
    report.global_urls = set()
    report.gpt_researcher = SimpleNamespace(
        agent="Research agent",
        role="Research role",
        mcp_configs=None,
        mcp_strategy=None,
        extract_headers=extract_headers,
    )
    return report


async def test_draft_section_titles_survive_header_extraction(monkeypatch):
    monkeypatch.setattr(detailed_report, "GPTResearcher", _StubResearcher)
    report = _bare_detailed_report()

    _assistant, titles = await report._research_subtopic({"task": "Battery chemistry"})

    assert titles == ["Battery chemistry", "Charging networks"]


async def test_string_draft_section_titles_still_work(monkeypatch):
    """Callers that already hand over markdown keep working unchanged."""

    class _StringStub(_StubResearcher):
        async def get_draft_section_titles(self, current_subtopic):
            return "\n".join(DRAFT_TITLES)

    monkeypatch.setattr(detailed_report, "GPTResearcher", _StringStub)
    report = _bare_detailed_report()

    _assistant, titles = await report._research_subtopic({"task": "Battery chemistry"})

    assert titles == ["Battery chemistry", "Charging networks"]
