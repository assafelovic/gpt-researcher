"""`cli.py --report_type detailed_report` must research with the CLI's source and tone."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import cli
from gpt_researcher import GPTResearcher
from gpt_researcher.config.variables.default import DEFAULT_CONFIG
from gpt_researcher.document import DocumentLoader
from gpt_researcher.skills.researcher import ResearchConductor
from gpt_researcher.utils.enum import Tone

LOCAL_DOCUMENTS = [{"raw_content": "Local text", "url": "notes.txt"}]


@pytest.fixture
def offline_cli(tmp_path, monkeypatch):
    # Keep the real CLI, DetailedReport, Config and conductor routing.
    # Replace only model generation, local document I/O and external searching.
    monkeypatch.chdir(tmp_path)
    for key in DEFAULT_CONFIG:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    monkeypatch.setattr(
        "gpt_researcher.agent.choose_agent",
        AsyncMock(return_value=("Research agent", "Research role")),
    )
    monkeypatch.setattr(
        GPTResearcher,
        "get_subtopics",
        AsyncMock(
            return_value=SimpleNamespace(subtopics=[SimpleNamespace(task="Section")])
        ),
    )
    for method, result in (
        ("write_introduction", "Introduction"),
        ("get_draft_section_titles", "## Findings"),
        ("get_similar_written_contents_by_draft_section_titles", []),
        ("write_report", "## Findings\n\nSection content."),
        ("write_report_conclusion", "Conclusion"),
    ):
        monkeypatch.setattr(GPTResearcher, method, AsyncMock(return_value=result))
    monkeypatch.setattr(cli, "_generate_task_title", AsyncMock(return_value="Report"))

    searches = []

    async def search(conductor, query, documents, query_domains=None):
        searches.append((conductor.researcher, documents))
        return ["Offline context"]

    monkeypatch.setattr(ResearchConductor, "_get_context_by_web_search", search)
    monkeypatch.setattr(DocumentLoader, "load", AsyncMock(return_value=LOCAL_DOCUMENTS))
    return searches


@pytest.mark.asyncio
@pytest.mark.parametrize("report_source", ["web", "local"])
async def test_detailed_report_researches_with_cli_source_and_tone(
    offline_cli, report_source
):
    args = cli.cli.parse_args(
        [
            "AI and jobs",
            "--report_type", "detailed_report",
            "--report_source", report_source,
            "--tone", "analytical",
            "--no-pdf",
            "--no-docx",
        ]
    )

    await cli.main(args)

    # The top-level researcher and the subtopic researcher both search.
    assert [(r.query, r.report_source, r.tone) for r, _ in offline_cli] == [
        ("AI and jobs", report_source, Tone.Analytical),
        ("Section", report_source, Tone.Analytical),
    ]
    documents = LOCAL_DOCUMENTS if report_source == "local" else []
    assert [docs for _, docs in offline_cli] == [documents, documents]
