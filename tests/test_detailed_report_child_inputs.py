"""Detailed report sections must retain the caller's configuration and documents."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.report_type import DetailedReport
from gpt_researcher import GPTResearcher
from gpt_researcher.config.variables.default import DEFAULT_CONFIG
from gpt_researcher.document import DocumentLoader, OnlineDocumentLoader
from gpt_researcher.skills.researcher import ResearchConductor


@pytest.fixture
def offline_report(monkeypatch):
    # Keep the real constructors, Config, conductor routing and report assembly.
    # Replace only agent/model generation, document I/O and external searching.
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
            return_value=SimpleNamespace(
                subtopics=[
                    SimpleNamespace(task="First section"),
                    SimpleNamespace(task="Second section"),
                ]
            )
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

    researchers, document_loads = [], []

    async def search(conductor, query, documents, query_domains=None):
        researchers.append(conductor.researcher)
        return ["Offline context"]

    async def online_documents(loader):
        document_loads.append(("online", loader.urls))
        return [{"raw_content": "Document text", "url": loader.urls[0]}]

    async def local_documents(loader):
        document_loads.append(("local", loader.path))
        return [{"raw_content": "Local text", "url": "notes.txt"}]

    monkeypatch.setattr(ResearchConductor, "_get_context_by_web_search", search)
    monkeypatch.setattr(OnlineDocumentLoader, "load", online_documents)
    monkeypatch.setattr(DocumentLoader, "load", local_documents)
    return researchers, document_loads


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "configuration", ["explicit", "environment", "defaults", "override"]
)
async def test_subtopics_keep_report_configuration(
    tmp_path, monkeypatch, offline_report, configuration
):
    config = tmp_path / "report.json"
    config.write_text(json.dumps({"LANGUAGE": "japanese", "TOTAL_WORDS": 321}))
    config_path = None
    if configuration in {"explicit", "override"}:
        config_path = str(config)
    elif configuration == "environment":
        monkeypatch.setenv("CONFIG_PATH", str(config))
    if configuration == "override":
        monkeypatch.setenv("LANGUAGE", "french")
        monkeypatch.setenv("TOTAL_WORDS", "654")

    report = DetailedReport("Topic", "detailed_report", "web", config_path=config_path)
    expected = (
        report.gpt_researcher.cfg.language,
        report.gpt_researcher.cfg.total_words,
    )
    assert (
        expected
        == {
            "explicit": ("japanese", 321),
            "environment": ("japanese", 321),
            "defaults": (DEFAULT_CONFIG["LANGUAGE"], DEFAULT_CONFIG["TOTAL_WORDS"]),
            "override": ("french", 654),
        }[configuration]
    )
    result = await report.run()

    researchers, _ = offline_report
    assert len(researchers) == 3
    assert [researcher.query for researcher in researchers] == [
        "Topic",
        "First section",
        "Second section",
    ]
    assert [(r.cfg.language, r.cfg.total_words) for r in researchers] == [expected] * 3
    assert result.count("Section content.") == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("document_urls", [None, [], ["https://example.com/notes.txt"]])
async def test_hybrid_subtopics_keep_report_documents(offline_report, document_urls):
    report = DetailedReport(
        "Topic", "detailed_report", "hybrid", document_urls=document_urls
    )
    await report.run()

    researchers, document_loads = offline_report
    # Hybrid research runs a document pass and a web pass for each researcher.
    assert len(researchers) == 6
    expected = (
        ("online", document_urls)
        if document_urls
        else ("local", report.gpt_researcher.cfg.doc_path)
    )
    assert document_loads == [expected] * 3


@pytest.mark.asyncio
@pytest.mark.parametrize("report_source", ["web", "local"])
async def test_document_urls_do_not_change_non_hybrid_source(
    offline_report, report_source
):
    report = DetailedReport(
        "Topic",
        "detailed_report",
        report_source,
        document_urls=["https://example.com/notes.txt"],
    )
    await report.run()

    researchers, document_loads = offline_report
    assert len(researchers) == 3
    expected = (
        [("local", report.gpt_researcher.cfg.doc_path)] * 3
        if report_source == "local"
        else []
    )
    assert document_loads == expected
