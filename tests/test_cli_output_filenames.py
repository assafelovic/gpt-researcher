"""Sequential CLI reports must keep all output formats grouped without overwrites."""

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from docx import Document

import cli


@pytest.fixture
def offline_research(monkeypatch):
    reports = iter(f"# Report {i}\n\nUnique report content {i}" for i in range(10))
    researcher = SimpleNamespace(
        cfg=SimpleNamespace(
            fast_llm_model="offline", fast_llm_provider="offline", llm_kwargs={}
        ),
        visited_urls=set(),
        conduct_research=AsyncMock(),
        write_report=AsyncMock(side_effect=lambda: next(reports)),
        add_costs=lambda cost: None,
        get_costs=lambda: 0,
    )
    monkeypatch.setattr(cli, "GPTResearcher", lambda **kwargs: researcher)
    title = AsyncMock(side_effect=RuntimeError("title service unavailable"))
    monkeypatch.setattr(cli, "create_chat_completion", title)
    return title


async def run_cli(query, *flags):
    await cli.main(cli.cli.parse_args([query, "--report_type", "research_report", *flags]))


@pytest.mark.asyncio
@pytest.mark.parametrize("length,runs", [(12, 3), (58, 3), (59, 3), (60, 10)])
async def test_fallback_titles_keep_native_docx_grouped(
    tmp_path, monkeypatch, offline_research, length, runs
):
    monkeypatch.chdir(tmp_path)
    previous_files = {}
    for i in range(runs):
        await run_cli("x" * length, "--no-pdf")
        for path, original_bytes in previous_files.items():
            assert path.read_bytes() == original_bytes
        markdown = list(Path("outputs").glob("*.md"))
        assert len(markdown) == i + 1
        current = next(path for path in markdown if path not in previous_files)
        assert len(current.stem) <= 60
        if i:
            assert current.stem.endswith(f"_{i + 1}")
        docx = current.with_suffix(".docx")
        assert docx.exists()
        text = "\n".join(p.text for p in Document(docx).paragraphs)
        assert f"Unique report content {i}" in text
        previous_files[current] = current.read_bytes()
        previous_files[docx] = docx.read_bytes()
    assert offline_research.await_count == runs
    assert not list(Path("outputs").glob("*.pdf"))


@pytest.fixture
def pdf_renderer(monkeypatch):
    paths = []

    def render(file_path, **kwargs):
        paths.append(Path(file_path))

    core = ModuleType("md2pdf.core")
    core.md2pdf = render
    package = ModuleType("md2pdf")
    package.core = core
    monkeypatch.setitem(sys.modules, "md2pdf", package)
    monkeypatch.setitem(sys.modules, "md2pdf.core", core)
    return paths


@pytest.mark.asyncio
async def test_pdf_renderer_receives_unique_markdown_stems(
    tmp_path, monkeypatch, offline_research, pdf_renderer
):
    monkeypatch.chdir(tmp_path)
    for _ in range(3):
        await run_cli("x" * 60, "--no-docx")
    markdown_stems = {path.stem for path in Path("outputs").glob("*.md")}
    assert len(markdown_stems) == 3
    assert {path.stem for path in pdf_renderer} == markdown_stems
    assert len(set(pdf_renderer)) == 3
    assert not list(Path("outputs").glob("*.docx"))


@pytest.mark.asyncio
async def test_short_generated_title_and_disabled_formats(
    tmp_path, monkeypatch, offline_research, pdf_renderer
):
    monkeypatch.chdir(tmp_path)
    offline_research.side_effect = None
    offline_research.return_value = '"Short title"'
    for _ in range(2):
        await run_cli("A long query", "--no-pdf", "--no-docx")
    assert sorted(path.name for path in Path("outputs").iterdir()) == [
        "Short_title.md",
        "Short_title_2.md",
    ]
    assert pdf_renderer == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "title,stem", [(" ... ", "untitled"), ('../bad\\name:*?<>|"', "badname")]
)
async def test_title_filename_safety(tmp_path, monkeypatch, offline_research, title, stem):
    monkeypatch.chdir(tmp_path)
    offline_research.side_effect = None
    offline_research.return_value = title
    await run_cli("Report query", "--no-pdf")
    assert sorted(path.name for path in Path("outputs").iterdir()) == [
        f"{stem}.docx",
        f"{stem}.md",
    ]
