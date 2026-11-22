"""``POST /report/`` must publish the whole report, whatever ``run_agent`` returns.

``run_agent(return_researcher=True)`` returns ``(report, researcher)`` for the
single-agent report types but a bare report string for ``multi_agents``, which
builds no ``GPTResearcher``. Indexing that string with ``[0]`` wrote a single
character into the DOCX/PDF and returned an empty report body.
"""

import asyncio

from backend.server import app as app_module

REPORT = "## Findings\n\nParagraph one.\n\nParagraph two.\n"


class FakeResearcher:
    """Stand-in for the researcher ``run_agent`` returns in the tuple branch."""

    def get_source_urls(self):
        return ["https://a.example"]

    def get_costs(self):
        return 0.5

    @property
    def visited_urls(self):
        return {"https://a.example"}

    def get_research_images(self):
        return [{"url": "https://a.example/i.png"}]


def _request(report_type):
    return app_module.ResearchRequest(
        task="Solid-state batteries",
        report_type=report_type,
        report_source="web",
        tone="Objective",
        repo_name="",
        branch_name="",
    )


def _patch_pipeline(monkeypatch, run_agent_result, written):
    async def fake_run_agent(*args, **kwargs):
        return run_agent_result

    async def fake_write_md(text, filename=""):
        written.append(text)
        return f"outputs/{filename}"

    monkeypatch.setattr(app_module, "run_agent", fake_run_agent)
    monkeypatch.setattr(app_module, "write_md_to_word", fake_write_md)
    monkeypatch.setattr(app_module, "write_md_to_pdf", fake_write_md)


def test_multi_agents_report_is_published_in_full(monkeypatch):
    written = []
    _patch_pipeline(monkeypatch, REPORT, written)

    response = asyncio.run(app_module.write_report(_request("multi_agents"), "rid"))

    assert written == [REPORT, REPORT], "DOCX/PDF must carry the whole report"
    assert response["report"] == REPORT


def test_single_agent_report_keeps_research_information(monkeypatch):
    written = []
    _patch_pipeline(monkeypatch, (REPORT, FakeResearcher()), written)

    response = asyncio.run(app_module.write_report(_request("research_report"), "rid"))

    assert written == [REPORT, REPORT]
    assert response["report"] == REPORT
    assert response["research_information"] == {
        "source_urls": ["https://a.example"],
        "research_costs": 0.5,
        "visited_urls": ["https://a.example"],
        "research_images": [{"url": "https://a.example/i.png"}],
    }
