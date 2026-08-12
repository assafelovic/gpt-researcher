from argparse import Namespace

import pytest

import cli as cli_module


@pytest.mark.asyncio
async def test_detailed_report_preserves_requested_report_source(tmp_path, monkeypatch):
    captured_kwargs = {}

    class FakeDetailedReport:
        gpt_researcher = None

        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

        async def run(self):
            return "# Local report"

    async def fake_generate_task_title(query, report, researcher):
        return "local-report"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli_module, "DetailedReport", FakeDetailedReport)
    monkeypatch.setattr(cli_module, "_generate_task_title", fake_generate_task_title)

    args = Namespace(
        query="Summarize my documents",
        report_type="detailed_report",
        tone="objective",
        encoding="utf-8",
        query_domains="",
        report_source="local",
        no_pdf=True,
        no_docx=True,
    )

    await cli_module.main(args)

    assert captured_kwargs["report_source"] == "local"
