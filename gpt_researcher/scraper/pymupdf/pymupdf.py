from __future__ import annotations

import os
import shutil
import tempfile
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import requests
from langchain_community.document_loaders import PyMuPDFLoader

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging
    from urllib.parse import ParseResult

    from langchain_core.documents.base import Document

logger: logging.Logger = get_formatted_logger(__name__)


class PyMuPDFScraper:
    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
        *_: Any,
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        """Initialize the scraper with a link and an optional session.

        Args:
            link (str): The URL or local file path of the PDF document.
            session (requests.Session, optional): An optional session for making HTTP requests.
        """
        self.link: str = link
        self.session: requests.Session = (
            session if session is not None else requests.Session()
        )
        self.kwargs: dict[str, Any] = kwargs

    def is_url(self) -> bool:
        """Check if the provided `link` is a valid URL.

        Returns:
            bool: True if the link is a valid URL, False otherwise.
        """
        try:
            result: ParseResult = urlparse(self.link)
            return all(
                [
                    result.scheme,
                    result.netloc,
                ]
            )  # Check for valid scheme and network location
        except Exception:
            return False

    def scrape(self) -> tuple[str, list[str], str]:
        """Scrape a document from the provided link (either URL or local file).

        Returns:
            tuple[str, list[str], str]: A tuple containing the content, image URLs, and title of the scraped document.
        """
        temp_filename: str | None = None
        try:
            image_urls: list[str] = []
            if self.is_url():
                # Use the session for making requests if provided
                headers: dict[str, str] = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/pdf,*/*",
                }

                # Create a temporary file with a unique name
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_filename = temp_file.name
                temp_file.close()  # Close the file before writing to it

                # Download the PDF

                logger.info(f"Downloading PDF from {self.link} to {temp_filename}")

                # Download the PDF with proper error handling
                try:
                    response: requests.Response = self.session.get(
                        self.link, headers=headers, timeout=30, stream=True
                    )
                    response.raise_for_status()

                    # Check if the response is actually a PDF
                    content_type = response.headers.get("Content-Type", "")
                    if (
                        "application/pdf" not in content_type
                        and not self.link.lower().endswith(".pdf")
                    ):
                        logger.warning(
                            f"Response may not be a PDF. Content-Type: {content_type}"
                        )

                    # Write the content to the temporary file
                    with open(temp_filename, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    # Ensure the file is fully written before loading
                    time.sleep(0.5)

                    # Check if the file exists and has content
                    if not os.path.exists(temp_filename):
                        raise FileNotFoundError(
                            f"Failed to create temporary file at {temp_filename}"
                        )

                    file_size = os.path.getsize(temp_filename)
                    if file_size == 0:
                        raise ValueError(
                            f"Downloaded PDF is empty (0 bytes) from {self.link}"
                        )

                    logger.info(f"Successfully downloaded PDF ({file_size} bytes)")

                except requests.exceptions.RequestException as e:
                    logger.error(
                        f"Request error downloading PDF: {e.__class__.__name__}: {e}"
                    )
                    return "", [], ""

                # Load the PDF using PyMuPDFLoader
                try:
                    loader = PyMuPDFLoader(temp_filename)
                    doc: list[Document] = loader.load()
                    logger.info(f"Successfully loaded PDF with {len(doc)} pages")
                except Exception as e:
                    logger.error(
                        f"Error loading PDF with PyMuPDFLoader: {e.__class__.__name__}: {e}"
                    )
                    return "", [], ""
            else:
                # Local file
                if not os.path.exists(self.link):
                    logger.error(f"Local PDF file not found: {self.link}")
                    return "", [], ""

                try:
                    loader = PyMuPDFLoader(self.link)
                    doc: list[Document] = loader.load()
                    logger.info(f"Successfully loaded local PDF with {len(doc)} pages")
                except Exception as e:
                    logger.error(
                        f"Error loading local PDF: {e.__class__.__name__}: {e}"
                    )
                    return "", [], ""

            # Extract image URLs if available
            try:
                for page in doc:
                    for img in getattr(page, "images", []):
                        image_urls.append(img.url)

                # Convert document to string representation
                content = "\n\n".join([str(page.page_content) for page in doc])
                return content, image_urls, ""
            except Exception as e:
                logger.error(
                    f"Error extracting content from PDF: {e.__class__.__name__}: {e}"
                )
                return "", [], ""

        except Exception as e:
            logger.exception(
                f"Unexpected error processing PDF: {self.link} {e.__class__.__name__}: {e}"
            )
            return "", [], ""
        finally:
            # Clean up the temporary file
            if temp_filename and os.path.exists(temp_filename):
                try:
                    if os.path.isfile(temp_filename):
                        os.remove(temp_filename)
                    else:
                        shutil.rmtree(temp_filename, ignore_errors=True)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove temporary file {temp_filename}: {e.__class__.__name__}: {e}"
                    )

        return "", [], ""
