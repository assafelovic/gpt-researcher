from __future__ import annotations

import os
import tempfile

from urllib.parse import ParseResult, urlparse

import requests

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document


class PyMuPDFScraper:
    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
    ):
        """Initialize the scraper with a link and an optional session.

        Args:
            link (str): The URL or local file path of the PDF document.
            session (requests.Session, optional): An optional session for making HTTP requests.
        """
        self.link: str = link
        self.session: requests.Session | None = session

    def is_url(self) -> bool:
        """Check if the provided `link` is a valid URL.

        Returns:
            bool: True if the link is a valid URL, False otherwise.
        """
        try:
            result: ParseResult = urlparse(self.link)
            return all([result.scheme, result.netloc])  # Check for valid scheme and network location
        except Exception as e:
            print(f"Error checking if link is URL: '{self.link}' {e.__class__.__name__}: {e}")
            return False

    def scrape(self) -> str | None:
        try:
            if self.is_url():
                response: requests.Response = requests.get(self.link, timeout=5, stream=True)
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_filename: str = temp_file.name  # Get the temporary file name
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)  # Write the downloaded content to the temporary file

                loader: PyMuPDFLoader = PyMuPDFLoader(temp_filename)
                doc: list[Document] = loader.load()

                os.remove(temp_filename)
            else:
                loader = PyMuPDFLoader(self.link)
                doc = loader.load()

            return str(doc)

        except requests.exceptions.Timeout as e:
            print(f"Download timed out. Please check the link : '{self.link}' : {e.__class__.__name__}: {e}")
        except Exception as e:
            print(f"Error loading PDF : '{self.link}' : {e.__class__.__name__}: {e}")
        return None
