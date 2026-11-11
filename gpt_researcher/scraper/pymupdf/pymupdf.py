import os
import tempfile
from urllib.parse import unquote, urlparse

import requests
from langchain_community.document_loaders import PyMuPDFLoader


def _fallback_title(link: str) -> str:
    """Derive a readable title fallback from a URL or file path when PDF metadata lacks a title."""
    try:
        parsed = urlparse(link)
        raw_name = os.path.basename(parsed.path or link)
        name = unquote(raw_name)
        stem = os.path.splitext(name)[0].replace("_", " ").replace("-", " ")
        cleaned = " ".join(stem.split())
        return cleaned or parsed.netloc or link
    except (ValueError, TypeError, AttributeError):
        return link


class PyMuPDFScraper:

    def __init__(self, link, session=None):
        """
        Initialize the scraper with a link and an optional session.

        Args:
          link (str): The URL or local file path of the PDF document.
          session (requests.Session, optional): An optional session for making HTTP requests.
        """
        self.link = link
        self.session = session

    def is_url(self) -> bool:
        """
        Check if the provided `link` is a valid URL.

        Returns:
          bool: True if the link is a valid URL, False otherwise.
        """
        try:
            result = urlparse(self.link)
            return all([result.scheme, result.netloc])  # Check for valid scheme and network location
        except Exception:
            return False

    def scrape(self) -> tuple[str, list[str], str]:
        """
        The `scrape` function uses PyMuPDFLoader to load a document from the provided link (either URL or local file)
        and returns the document as a string.

        Returns:
          str: A string representation of the loaded document.
        """
        try:
            if self.is_url():
                http = self.session or requests
                try:
                    response = http.get(self.link, timeout=(5, 30), stream=True)
                    response.raise_for_status()
                except requests.exceptions.SSLError:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"SSL verification failed for {self.link}, retrying without verification"
                    )
                    response = http.get(self.link, timeout=(5, 30), stream=True, verify=False)
                    response.raise_for_status()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_filename = temp_file.name  # Get the temporary file name
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)  # Write the downloaded content to the temporary file

                # Always clean up the downloaded temp file, even if loading fails
                # (PyMuPDFLoader.load() can raise on a malformed/partial PDF).
                try:
                    loader = PyMuPDFLoader(temp_filename)
                    doc = loader.load()
                finally:
                    try:
                        os.remove(temp_filename)
                    except OSError:
                        pass
            else:
                loader = PyMuPDFLoader(self.link)
                doc = loader.load()

            # Extract the content, image (if any), and title from the document.
            image = []
            # Retrieve content from ALL pages to ensure PDFs with cover pages pass validation.
            content = "\n".join(page.page_content for page in doc)
            title = (doc[0].metadata.get("title") or "").strip() if doc else ""
            if doc and not title:
                title = _fallback_title(self.link)
            return content, image, title

        except requests.exceptions.Timeout:
            print(f"Download timed out. Please check the link : {self.link}")
            return "", [], ""
        except Exception as e:
            print(f"Error loading PDF : {self.link} {e}")
            return "", [], ""
