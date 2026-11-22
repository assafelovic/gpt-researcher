"""PDFLoader extracts text with pypdfium2 and falls back to pypdf."""

import importlib.util
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pypdf
import pytest

from gpt_researcher.document import pdf_loader
from gpt_researcher.document.pdf_loader import PDFLoader
from gpt_researcher.scraper.pdf.pdf import PDFScraper

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PDF = ROOT / "deep_agents" / "benchmark_data" / "internal_docs" / "ops" / "q1_2026_ops_report.pdf"


def _write_pdf(text: str, path: Path) -> Path:
    spec = importlib.util.spec_from_file_location(
        "build_corpus", ROOT / "deep_agents" / "benchmark_data" / "build_corpus.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_pdf(text, path)
    return path


@pytest.fixture
def three_page_pdf(tmp_path):
    lines = [f"Line {n} of the quarterly report" for n in range(1, 131)]
    return _write_pdf("\n".join(lines), tmp_path / "three_pages.pdf")


def test_loads_one_document_per_page_with_metadata(three_page_pdf):
    docs = PDFLoader(three_page_pdf).load()

    assert [d.metadata["page"] for d in docs] == [0, 1, 2]
    assert all(d.metadata["total_pages"] == 3 for d in docs)
    assert all(d.metadata["source"] == str(three_page_pdf) for d in docs)
    assert "Line 1 of the quarterly report" in docs[0].page_content
    assert "Line 53 of the quarterly report" in docs[1].page_content
    assert "Line 130 of the quarterly report" in docs[2].page_content
    assert "\r" not in "".join(d.page_content for d in docs)


def test_reads_the_metadata_title(tmp_path):
    reader = pypdf.PdfReader(CORPUS_PDF)
    writer = pypdf.PdfWriter(clone_from=reader)
    writer.add_metadata({"/Title": "  Q1 2026 Operations Report  ", "/Author": "COO office"})
    path = tmp_path / "titled.pdf"
    with open(path, "wb") as f:
        writer.write(f)

    docs = PDFLoader(path).load()

    assert docs[0].metadata["title"] == "Q1 2026 Operations Report"
    assert docs[0].metadata["author"] == "COO office"
    assert "Fleet availability" in docs[0].page_content


def test_reads_an_encrypted_pdf_with_an_empty_user_password(tmp_path):
    pytest.importorskip("cryptography")
    writer = pypdf.PdfWriter(clone_from=CORPUS_PDF)
    writer.encrypt(user_password="", owner_password="owner", algorithm="AES-256")
    path = tmp_path / "encrypted.pdf"
    with open(path, "wb") as f:
        writer.write(f)

    assert "Fleet availability" in PDFLoader(path).load()[0].page_content


def test_keeps_non_ascii_text():
    text = PDFLoader(CORPUS_PDF).load()[0].page_content

    assert "-25°C cold-chamber certification" in text


def test_pdfium_line_break_markers_become_hyphen_newlines():
    raw = "Bewegungs\x02mangel and Bewegungs\ufffemangel\r\nnext\rline"

    assert pdf_loader._clean_pdfium_text(raw) == "Bewegungs-\nmangel and Bewegungs-\nmangel\nnext\nline"


def test_falls_back_to_pypdf_when_pdfium_fails(three_page_pdf, monkeypatch):
    def broken(_):
        raise RuntimeError("pdfium failed")

    monkeypatch.setattr(pdf_loader, "_extract_with_pdfium", broken)

    docs = PDFLoader(three_page_pdf).load()

    assert len(docs) == 3
    assert "Line 130 of the quarterly report" in docs[2].page_content


def test_pypdf_fallback_keeps_pages_after_a_failing_page(three_page_pdf, monkeypatch):
    def broken(_):
        raise RuntimeError("pdfium failed")

    original = pypdf.PageObject.extract_text
    calls = []

    def flaky(self, *args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise ValueError("bad content stream")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(pdf_loader, "_extract_with_pdfium", broken)
    monkeypatch.setattr(pypdf.PageObject, "extract_text", flaky)

    docs = PDFLoader(three_page_pdf).load()

    assert [d.page_content == "" for d in docs] == [True, False, False]
    assert "Line 130 of the quarterly report" in docs[2].page_content


def test_concurrent_loads_return_complete_text(three_page_pdf):
    expected = [d.page_content for d in PDFLoader(three_page_pdf).load()]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: [d.page_content for d in PDFLoader(three_page_pdf).load()], range(16)))

    assert all(result == expected for result in results)


def test_unreadable_file_raises(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a pdf")

    with pytest.raises(Exception):
        PDFLoader(path).load()


def test_pdf_scraper_reads_a_local_file_and_falls_back_to_the_file_name_title(three_page_pdf):
    content, images, title = PDFScraper(str(three_page_pdf)).scrape()

    assert "Line 1 of the quarterly report" in content
    assert "Line 130 of the quarterly report" in content
    assert images == []
    assert title == "three pages"
