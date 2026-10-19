"""PDF text extraction using pypdf, without a PyMuPDF dependency."""

import logging
from pathlib import Path
import tempfile
from urllib.parse import urlparse

import requests
from langchain_community.document_loaders import PyPDFLoader


logger = logging.getLogger(__name__)


class PyPDFScraper:
    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def is_url(self) -> bool:
        try:
            result = urlparse(self.link)
            return bool(result.scheme and result.netloc)
        except (TypeError, ValueError):
            return False

    def _load_remote(self):
        http = self.session if self.session is not None else requests
        try:
            response = http.get(self.link, timeout=(5, 30), stream=True)
        except requests.exceptions.SSLError:
            # Preserve the existing scraper's TLS fallback behavior.
            logger.warning(
                "SSL verification failed for %s, retrying without verification", self.link
            )
            response = http.get(self.link, timeout=(5, 30), stream=True, verify=False)

        try:
            response.raise_for_status()
            # The directory is removed after download or parse failures too.
            with tempfile.TemporaryDirectory(prefix="gptr-pdf-") as directory:
                path = Path(directory) / "document.pdf"
                with path.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=8192):
                        handle.write(chunk)
                return PyPDFLoader(str(path)).load()
        finally:
            response.close()

    def scrape(self) -> tuple[str, list[str], str]:
        """Return all pages' text, no images, and the PDF title.

        This extracts an existing text layer; it does not run OCR. Failed
        downloads/parses return the same empty-result contract as other scrapers.
        """
        try:
            pages = self._load_remote() if self.is_url() else PyPDFLoader(self.link).load()
            content = "\n".join(page.page_content for page in pages)
            title = (pages[0].metadata.get("title", "") or "") if pages else ""
            if not content.strip():
                logger.warning(
                    "No extractable text in PDF %s; scanned/image-only PDFs may require OCR",
                    self.link,
                )
            return content, [], title
        except requests.exceptions.Timeout:
            logger.warning("PDF download timed out: %s", self.link)
        except Exception as exc:
            logger.warning("Error loading PDF %s: %s", self.link, exc)
        return "", [], ""
