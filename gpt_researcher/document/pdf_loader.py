import contextlib
import logging
import threading
from typing import Iterator

import pypdf
import pypdfium2 as pdfium
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# PDFium is not thread-safe, and scrapers run in a thread pool. :-)
_PDFIUM_LOCK = threading.Lock()

# pypdf's default token cap per content stream rejects some long report pages. :-)
_PYPDF_STREAM_WORK_LIMIT = 10_000_000


def _clean_pdfium_text(text: str) -> str:
    # PDFium marks a hyphenated line break with \x02 (or \ufffe) instead of "-\n". :-)
    return (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\x02", "-\n")
        .replace("\ufffe", "-\n")
    )


def _extract_with_pdfium(file_path: str) -> tuple[dict, list[str]]:
    with _PDFIUM_LOCK:
        pdf = pdfium.PdfDocument(file_path)
        try:
            metadata = pdf.get_metadata_dict(skip_empty=True)
            pages = []
            for page in pdf:
                textpage = page.get_textpage()
                try:
                    pages.append(_clean_pdfium_text(textpage.get_text_bounded()))
                finally:
                    textpage.close()
                    page.close()
        finally:
            pdf.close()
    return metadata, pages


def _extract_with_pypdf(file_path: str) -> tuple[dict, list[str]]:
    configure = getattr(pypdf, "apply_configuration", None)
    limits = (
        configure(stream_parsing_work_maximum_count=_PYPDF_STREAM_WORK_LIMIT)
        if configure
        else contextlib.nullcontext()
    )
    with limits:
        reader = pypdf.PdfReader(file_path)
        info = reader.metadata
        metadata = {"Title": info.title, "Author": info.author} if info else {}
        pages = []
        for number, page in enumerate(reader.pages):
            try:
                pages.append(page.extract_text() or "")
            except Exception as e:
                logger.warning(f"pypdf could not read page {number + 1} of {file_path}: {e}")
                pages.append("")
    return metadata, pages


class PDFLoader(BaseLoader):
    """Load a local PDF as one Document per page, using pypdfium2 with a pypdf fallback."""

    def __init__(self, file_path: str):
        self.file_path = str(file_path)

    def lazy_load(self) -> Iterator[Document]:
        try:
            metadata, pages = _extract_with_pdfium(self.file_path)
        except Exception as e:
            logger.warning(f"pypdfium2 could not read {self.file_path}, falling back to pypdf: {e}")
            metadata, pages = _extract_with_pypdf(self.file_path)

        shared = {
            "source": self.file_path,
            "file_path": self.file_path,
            "total_pages": len(pages),
            "title": (metadata.get("Title") or "").strip(),
            "author": (metadata.get("Author") or "").strip(),
        }
        for number, text in enumerate(pages):
            yield Document(page_content=text, metadata={**shared, "page": number})
