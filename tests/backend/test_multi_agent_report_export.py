import pytest

from backend.server import app as app_module


@pytest.mark.asyncio
async def test_multi_agent_report_exports_and_returns_full_report(monkeypatch):
    exported_reports = []

    async def fake_run_agent(**kwargs):
        return "complete multi-agent report"

    async def fake_write_md_to_word(report, research_id):
        exported_reports.append(("docx", report, research_id))
        return "outputs/report.docx"

    async def fake_write_md_to_pdf(report, research_id):
        exported_reports.append(("pdf", report, research_id))
        return "outputs/report.pdf"

    monkeypatch.setattr(app_module, "run_agent", fake_run_agent)
    monkeypatch.setattr(app_module, "write_md_to_word", fake_write_md_to_word)
    monkeypatch.setattr(app_module, "write_md_to_pdf", fake_write_md_to_pdf)

    request = app_module.ResearchRequest(
        task="test",
        report_type="multi_agents",
        report_source="web",
        tone="Objective",
        repo_name="",
        branch_name="",
        generate_in_background=False,
    )

    response = await app_module.write_report(request, research_id="report-id")

    assert exported_reports == [
        ("docx", "complete multi-agent report", "report-id"),
        ("pdf", "complete multi-agent report", "report-id"),
    ]
    assert response["report"] == "complete multi-agent report"


@pytest.mark.asyncio
async def test_standard_report_keeps_research_metadata(monkeypatch):
    class FakeResearcher:
        visited_urls = {"https://example.com"}

        def get_source_urls(self):
            return ["https://example.com"]

        def get_costs(self):
            return 0.25

        def get_research_images(self):
            return ["image.png"]

    async def fake_run_agent(**kwargs):
        return "standard report", FakeResearcher()

    async def fake_export(report, research_id):
        return f"outputs/{research_id}"

    monkeypatch.setattr(app_module, "run_agent", fake_run_agent)
    monkeypatch.setattr(app_module, "write_md_to_word", fake_export)
    monkeypatch.setattr(app_module, "write_md_to_pdf", fake_export)

    request = app_module.ResearchRequest(
        task="test",
        report_type="research_report",
        report_source="web",
        tone="Objective",
        repo_name="",
        branch_name="",
        generate_in_background=False,
    )

    response = await app_module.write_report(request, research_id="report-id")

    assert response["report"] == "standard report"
    assert response["research_information"] == {
        "source_urls": ["https://example.com"],
        "research_costs": 0.25,
        "visited_urls": ["https://example.com"],
        "research_images": ["image.png"],
    }
