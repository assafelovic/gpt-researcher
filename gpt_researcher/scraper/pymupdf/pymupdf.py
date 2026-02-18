import os
import logging
import requests
import tempfile
import warnings
from urllib.parse import urlparse
from langchain_community.document_loaders import PyMuPDFLoader

# Suppress PyMuPDF new() deprecation warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)


logger = logging.getLogger(__name__)


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

    def _download_pdf(self, url: str) -> requests.Response:
        """
        Download a PDF from URL with proper timeout and SSL verification fallback.

        Args:
          url (str): The URL to download from.

        Returns:
          requests.Response: The response object.

        Raises:
          requests.exceptions.RequestException: If download fails after all retries.
        """
        # Timeout as (connect_timeout, read_timeout) - 5s connect, 30s read for large PDFs
        timeout = (5, 30)

        # First attempt with SSL verification enabled
        try:
            response = requests.get(url, timeout=timeout, stream=True, verify=True)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError as e:
            # Log warning when SSL verification fails and we need to bypass it
            logger.warning(
                f"SSL verification failed for {url}. "
                f"This may indicate a certificate issue with the server. "
                f"Retrying with SSL verification disabled. Error: {e}"
            )
            # Retry with SSL verification disabled as fallback
            response = requests.get(url, timeout=timeout, stream=True, verify=False)
            response.raise_for_status()
            return response

    def scrape(self) -> tuple[str, list[str], str]:
        """
        The `scrape` function uses PyMuPDFLoader to load a document from the provided link (either URL or local file)
        and returns the document as a string.

        Returns:
          str: A string representation of the loaded document.
        """
        temp_filename = None
        try:
            if self.is_url():
                response = self._download_pdf(self.link)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_filename = temp_file.name  # Get the temporary file name
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)  # Write the downloaded content to the temporary file

                loader = PyMuPDFLoader(temp_filename)
                doc = loader.load()

                os.remove(temp_filename)
                temp_filename = None
            else:
                loader = PyMuPDFLoader(self.link)
                doc = loader.load()

            # Extract content from all pages, images (if any), and title from the document.
            image = []
            # Concatenate all pages to ensure sufficient content for downstream processing.
            content = "\n\n".join([page.page_content for page in doc])

            # Handle edge case where metadata might be missing
            title = doc[0].metadata.get("title", "") if doc else ""

            return content, image, title

        except requests.exceptions.Timeout:
            print(f"Download timed out. Please check the link : {self.link}")
            return "", [], ""
        except requests.exceptions.SSLError as e:
            # This catches SSLError that persists even after fallback
            logger.error(f"SSL error persisted even with verification disabled for {self.link}: {e}")
            print(f"SSL error loading PDF : {self.link} {e}")
            return "", [], ""
        except Exception as e:
            print(f"Error loading PDF : {self.link} {e}")
            return "", [], ""
        finally:
            # Clean up temp file if it still exists (edge case: exception during processing)
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except OSError:
                    pass  # Ignore cleanup errors
