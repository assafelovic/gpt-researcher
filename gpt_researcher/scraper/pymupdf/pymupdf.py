from __future__ import annotations

import logging
import os
import tempfile
from typing import Any
from urllib.parse import urlparse

import requests
from langchain_community.document_loaders import PyMuPDFLoader

logger = logging.getLogger(__name__)


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
        self.session: requests.Session | None = session
        self.kwargs: dict[str, Any] = kwargs

    def is_url(self) -> bool:
        """Check if the provided `link` is a valid URL.

        Returns:
            bool: True if the link is a valid URL, False otherwise.
        """
        try:
            result = urlparse(self.link)
            return all(
                [result.scheme, result.netloc]
            )  # Check for valid scheme and network location
        except Exception:
            return False

    def scrape(self) -> tuple[str, list[str], str]:
        """Scrape a document from the provided link (either URL or local file)

        Returns:
            tuple[str, list[str], str]: A tuple containing the content, image URLs, and title of the scraped document.
        """
        try:
            image_urls: list[str] = []
            if self.is_url():
                response = requests.get(self.link, timeout=5, stream=True)
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_filename = temp_file.name  # Get the temporary file name
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)  # Write the downloaded content to the temporary file

                loader = PyMuPDFLoader(temp_filename)
                doc = loader.load()

                os.remove(temp_filename)
            else:
                loader = PyMuPDFLoader(self.link)
                doc = loader.load()

                for page in doc:
                    for img in getattr(page, "images", []):
                        image_urls.append(img.url)

            return str(d.model_dump_json() for d in doc), image_urls, ""

        except requests.exceptions.Timeout:
            logger.exception(f"Download timed out. Please check the link : {self.link}")
        except Exception as e:
            logger.exception(f"Error loading PDF : {self.link} {e.__class__.__name__}: {e}")

        return "", [], ""
