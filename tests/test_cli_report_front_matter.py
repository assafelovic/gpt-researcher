"""The CLI's YAML front matter belongs in the Markdown file, not in the PDF or DOCX."""

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from docx import Document

import cli

REPORT = "# Solar storage\n\nBatteries smooth out supply."


@pytest.fixture
def offline_cli(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    researcher = SimpleNamespace(
        cfg=SimpleNamespace(
            fast_llm_model="offline", fast_llm_provider="offline", llm_kwargs={}
        ),
        visited_urls={"https://example.com/storage"},
        conduct_research=AsyncMock(),
        write_report=AsyncMock(return_value=REPORT),
        add_costs=lambda cost: None,
        get_costs=lambda: 0.01,
    )
    monkeypatch.setattr(cli, "GPTResearcher", lambda **kwargs: researcher)
    monkeypatch.setattr(
        cli, "create_chat_completion", AsyncMock(return_value="Solar storage")
    )


@pytest.fixture
def pdf_renderer(monkeypatch):
    rendered = []

    def render(file_path, **kwargs):
        rendered.append(kwargs["raw"])

    core = ModuleType("md2pdf.core")
    core.md2pdf = render
    package = ModuleType("md2pdf")
    package.core = core
    monkeypatch.setitem(sys.modules, "md2pdf", package)
    monkeypatch.setitem(sys.modules, "md2pdf.core", core)
    return rendered


async def run_cli(*flags):
    await cli.main(
        cli.cli.parse_args(["Solar storage", "--report_type", "research_report", *flags])
    )


@pytest.mark.asyncio
async def test_markdown_keeps_the_front_matter(offline_cli):
    await run_cli("--no-pdf", "--no-docx")

    markdown = Path("outputs/Solar_storage.md").read_text(encoding="utf-8")
    assert markdown.startswith('---\ntask_id: "')
    assert 'query: "Solar storage"\n' in markdown
    assert markdown.endswith("---\n" + REPORT)


@pytest.mark.asyncio
async def test_docx_starts_with_the_report(offline_cli):
    await run_cli("--no-pdf")

    paragraphs = Document("outputs/Solar_storage.docx").paragraphs
    assert [(p.style.name, p.text) for p in paragraphs] == [
        ("Heading 1", "Solar storage"),
        ("Normal", "Batteries smooth out supply."),
    ]


@pytest.mark.asyncio
async def test_pdf_renders_the_report_without_the_front_matter(
    offline_cli, pdf_renderer
):
    await run_cli("--no-docx")

    assert pdf_renderer == [REPORT]
