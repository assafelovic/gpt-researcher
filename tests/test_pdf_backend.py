"""Real PDF extraction through the supported entry points, without fitz."""

import importlib.abc
import importlib.util
from io import BytesIO
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import requests
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject, TextStringObject

from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.document.online_document import OnlineDocumentLoader
from gpt_researcher.scraper import PyPDFScraper, PyMuPDFScraper
from gpt_researcher.scraper.browser.processing import scrape_skills


@pytest.fixture(autouse=True)
def forbid_pymupdf(monkeypatch):
    class BlockPyMuPDF(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".")[0] in {"fitz", "pymupdf"}:
                raise ImportError("PyMuPDF is intentionally unavailable in this test")

    for name in list(sys.modules):
        if name.split(".")[0] in {"fitz", "pymupdf"}:
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(sys, "meta_path", [BlockPyMuPDF(), *sys.meta_path])


def make_pdf(*texts, title="Research notes", password=None):
    writer = PdfWriter()
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    }))
    for text in texts:
        page = writer.add_blank_page(width=595, height=842)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})
        })
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 50 750 Td <{text.encode().hex()}> Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    if title is not None:
        writer.add_metadata({"/Title": title})
    if password is not None:
        writer.encrypt(password, algorithm="AES-256")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def pdf_file(tmp_path):
    path = tmp_path / "notes.pdf"
    path.write_bytes(make_pdf("Cover page", "Findings on the second page."))
    return path


def response_for(payload):
    response = MagicMock()
    response.iter_content.return_value = [payload[:80], payload[80:]]
    return response


def test_local_pdf_all_pages_and_title(pdf_file):
    text, images, title = PyPDFScraper(str(pdf_file)).scrape()
    assert "Cover page" in text
    assert "Findings on the second page." in text
    assert text.index("Cover page") < text.index("Findings")
    assert images == []
    assert title == "Research notes"


def test_chinese_text_layer_is_extracted(tmp_path):
    writer = PdfWriter()
    cmap = DecodedStreamObject()
    cmap.set_data(b"""/CIDInit /ProcSet findresource begin 12 dict begin begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /Test-UCS def /CMapType 2 def
1 begincodespacerange <0000> <FFFF> endcodespacerange
4 beginbfchar <0001> <4E2D> <0002> <6587> <0003> <5185> <0004> <5BB9> endbfchar
endcmap CMapName currentdict /CMap defineresource pop end end""")
    cid_font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/CIDFontType2"),
        NameObject("/BaseFont"): NameObject("/TestCJK"),
        NameObject("/CIDSystemInfo"): DictionaryObject({
            NameObject("/Registry"): TextStringObject("Adobe"),
            NameObject("/Ordering"): TextStringObject("Identity"),
            NameObject("/Supplement"): NumberObject(0),
        }),
    })
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type0"),
        NameObject("/BaseFont"): NameObject("/TestCJK"),
        NameObject("/Encoding"): NameObject("/Identity-H"),
        NameObject("/DescendantFonts"): ArrayObject([writer._add_object(cid_font)]),
        NameObject("/ToUnicode"): writer._add_object(cmap),
    }))
    page = writer.add_blank_page(width=595, height=842)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})
    })
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 50 750 Td <0001000200030004> Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    path = tmp_path / "chinese.pdf"
    writer.write(path)
    assert "中文内容" in PyPDFScraper(str(path)).scrape()[0]


def test_legacy_class_and_browser_helper_use_new_backend(pdf_file):
    assert PyMuPDFScraper is PyPDFScraper
    assert "Findings" in PyMuPDFScraper(str(pdf_file)).scrape()[0]
    assert "Findings" in scrape_skills.scrape_pdf_with_pymupdf(str(pdf_file))


@pytest.mark.parametrize("title", [None, "中文标题"])
def test_missing_or_unicode_title(tmp_path, title):
    path = tmp_path / "metadata.pdf"
    path.write_bytes(make_pdf("Body", title=title))
    assert PyPDFScraper(str(path)).scrape()[2] == (title or "")


def test_remote_pdf_uses_session_and_closes_response(pdf_file, monkeypatch, tmp_path):
    from gpt_researcher.scraper.pypdf import pypdf as module

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(module.tempfile, "tempdir", str(scratch))
    response = response_for(pdf_file.read_bytes())
    session = MagicMock()
    session.get.return_value = response
    url = "https://example.com/notes.PDF?signature=test"
    text, _, title = PyPDFScraper(url, session).scrape()

    session.get.assert_called_once_with(url, timeout=(5, 30), stream=True)
    response.raise_for_status.assert_called_once()
    response.close.assert_called_once()
    session.close.assert_not_called()
    assert "Findings" in text and title == "Research notes"
    assert list(scratch.iterdir()) == []


def test_remote_pdf_timeout_has_empty_contract(caplog):
    session = MagicMock()
    session.get.side_effect = requests.Timeout("slow download")
    assert PyPDFScraper("https://example.com/notes.pdf", session).scrape() == ("", [], "")
    assert "timed out" in caplog.text


@pytest.mark.parametrize("payload", [b"not a PDF", make_pdf("Secret", password="required")])
def test_unreadable_pdf_returns_empty_and_logs(tmp_path, caplog, payload):
    path = tmp_path / "unreadable.pdf"
    path.write_bytes(payload)
    assert PyPDFScraper(str(path)).scrape() == ("", [], "")
    assert "Error loading PDF" in caplog.text


def test_empty_password_aes_pdf_is_readable(tmp_path):
    path = tmp_path / "encrypted.pdf"
    path.write_bytes(make_pdf("Readable without a password", password=""))
    assert "Readable" in PyPDFScraper(str(path)).scrape()[0]


def test_image_only_pdf_warns_about_empty_text(tmp_path, caplog):
    from PIL import Image

    path = tmp_path / "scan.pdf"
    Image.new("RGB", (100, 100), color="white").save(path, "PDF")
    text, images, _ = PyPDFScraper(str(path)).scrape()
    assert not text.strip()
    assert images == []
    assert "No extractable text" in caplog.text and "OCR" in caplog.text


@pytest.mark.asyncio
async def test_local_document_loader_reads_pdf_without_pymupdf(pdf_file):
    documents = await DocumentLoader([str(pdf_file)]).load()
    assert [d["raw_content"] for d in documents] == ["Cover page", "Findings on the second page."]
    assert all(d["url"] == "notes.pdf" for d in documents)


@pytest.mark.asyncio
async def test_online_document_loader_reads_pdf_and_removes_download(pdf_file):
    # This entry point owns the already-downloaded temporary file.
    pages = await OnlineDocumentLoader([])._load_document(str(pdf_file), "pdf")
    assert [p.page_content for p in pages] == ["Cover page", "Findings on the second page."]
    assert all(p.metadata["source"] == str(pdf_file) for p in pages)
    assert not pdf_file.exists()


@pytest.mark.asyncio
async def test_pdf_fallback_uses_real_parser_without_pymupdf(monkeypatch):
    from gpt_researcher.scraper.scraper import Scraper
    from gpt_researcher.scraper import scraper as module

    class Pool:
        executor = None

        def throttle(self):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class HTMLBackend:
        def __init__(self, *args):
            pass

        def scrape(self):
            return "%PDF-1.7 endobj endstream " * 20, [], ""

    monkeypatch.setattr(module, "validate_url", lambda *a, **k: None)
    scraper = Scraper([], "test-user-agent", "bs", Pool())
    monkeypatch.setattr(scraper, "get_scraper", lambda url: HTMLBackend)
    text = "Actual full text from the recovered PDF. " * 10
    response = response_for(make_pdf(text))
    session = MagicMock()
    session.get.return_value = response
    result = await scraper.extract_data_from_url("https://example.com/download", session)
    assert text.strip() in result["raw_content"]
    assert result["title"] == "Research notes"
    response.close.assert_called_once()


def test_browser_arxiv_loads_full_pdf_without_langchain_fitz(monkeypatch, pdf_file):
    client = MagicMock()
    client.results.return_value = iter([SimpleNamespace(pdf_url="https://arxiv.org/pdf/2601.12345")])
    monkeypatch.setattr("arxiv.Client", lambda: client)
    session = MagicMock()
    session.get.return_value = response_for(pdf_file.read_bytes())

    text = scrape_skills.scrape_pdf_with_arxiv("https://arxiv.org/abs/2601.12345", session)
    assert "Findings on the second page." in text
    search = client.results.call_args.args[0]
    assert search.id_list == ["2601.12345"]
    session.get.assert_called_once_with("https://arxiv.org/pdf/2601.12345", timeout=(5, 30), stream=True)


def test_browser_arxiv_no_result_is_empty(monkeypatch):
    client = MagicMock()
    client.results.return_value = iter([])
    monkeypatch.setattr("arxiv.Client", lambda: client)
    assert scrape_skills.scrape_pdf_with_arxiv("2601.12345") == ""


def test_browser_arxiv_preserves_free_text_search(monkeypatch):
    client = MagicMock()
    client.results.return_value = iter([])
    monkeypatch.setattr("arxiv.Client", lambda: client)
    assert scrape_skills.scrape_pdf_with_arxiv("quantum computing") == ""
    assert client.results.call_args.args[0].query == "quantum computing"


def test_browser_dispatch_uses_shared_pdf_parser(monkeypatch, pdf_file):
    from gpt_researcher.scraper.browser import browser as module

    # Selenium navigation is unrelated to extraction; avoid starting a browser.
    monkeypatch.setattr(module, "WebDriverWait", MagicMock(), raising=False)
    monkeypatch.setattr(module, "EC", MagicMock(), raising=False)
    monkeypatch.setattr(module, "By", MagicMock(), raising=False)
    browser = module.BrowserScraper.__new__(module.BrowserScraper)
    browser.url = "https://example.com/report.PDF?signature=test"
    browser.driver = MagicMock()
    browser._scroll_to_bottom = lambda: None
    browser.session = MagicMock()
    browser.session.get.return_value = response_for(pdf_file.read_bytes())
    content, images, _ = browser.scrape_text_with_selenium()
    assert "Cover page" in content and "Findings" in content
    assert images == []
    browser.session.get.assert_called_once_with(browser.url, timeout=(5, 30), stream=True)


def test_benchmark_pdf_generation_round_trip(tmp_path):
    source = Path(__file__).resolve().parents[1] / "deep_agents/benchmark_data/build_corpus.py"
    spec = importlib.util.spec_from_file_location("pdf_corpus_builder", source)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    path = tmp_path / "corpus.pdf"
    lines = [f"Fact {i}: (cost $12) and \\path" for i in range(60)]
    builder.write_pdf("\n".join(lines), path)
    reader = PdfReader(path)
    assert len(reader.pages) == 2
    extracted = "\n".join(page.extract_text() for page in reader.pages)
    assert all(line in extracted for line in lines)
