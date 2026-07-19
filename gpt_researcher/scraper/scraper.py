"""Web scraper module for GPT Researcher.

This module provides the Scraper class that extracts content from URLs
using various scraping backends (BeautifulSoup, PyMuPDF, Browser, etc.).
"""

import asyncio
import importlib
import logging
import subprocess
import sys
from urllib.parse import urlparse

import requests
from colorama import Fore, init

from gpt_researcher.utils.workers import WorkerPool

from . import (
    ArxivScraper,
    BeautifulSoupScraper,
    BrowserScraper,
    FireCrawl,
    NoDriverScraper,
    PyMuPDFScraper,
    TavilyExtract,
    WebBaseLoaderScraper,
)

# get_scraper() picks a backend from the URL's suffix, but PDFs served from
# institutional repositories (DSpace/EPrints-style download endpoints) are
# routed by content type, not a file extension -- e.g.
# "scholarspace.manoa.hawaii.edu/bitstreams/<uuid>/download" has none. Those
# fall through to a text/HTML scraper, which has no way to decode the PDF
# body and returns its raw bytes (FlateDecode streams, xref tables, /Annot
# objects) as if it were the page's real text -- silently: no exception, a
# normal-looking content_length, just unusable content.
#
# These tokens are PDF's own internal structural syntax; they essentially
# never occur, even coincidentally, in real prose. Two independent hits is
# enough to be confident this is raw PDF, not text that happens to contain
# one of these words in isolation.
_PDF_STRUCTURE_MARKERS = ("endobj", "endstream", "/FlateDecode", "xref", "trailer")
_MIN_PDF_MARKER_HITS = 2


def _looks_like_unextracted_pdf(text: str) -> bool:
    if text.startswith("%PDF-"):
        return True
    hits = sum(1 for marker in _PDF_STRUCTURE_MARKERS if marker in text)
    return hits >= _MIN_PDF_MARKER_HITS


class Scraper:
    """
    Scraper class to extract the content from the links
    """

    def __init__(self, urls, user_agent, scraper, worker_pool: WorkerPool):
        """
        Initialize the Scraper class.
        Args:
            urls: List of URLs to scrape (duplicates will be removed)
        """
        # Optimization: Remove duplicate URLs to avoid redundant scraping
        unique_urls = list(dict.fromkeys(urls))  # Preserves order while removing duplicates
        duplicates_removed = len(urls) - len(unique_urls)

        self.urls = unique_urls
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.scraper = scraper
        if self.scraper == "tavily_extract":
            self._check_pkg(self.scraper)
        if self.scraper == "firecrawl":
            self._check_pkg(self.scraper)
        self.logger = logging.getLogger(__name__)
        self.worker_pool = worker_pool

        # Log deduplication results if duplicates were found
        if duplicates_removed > 0:
            self.logger.info(
                f"Removed {duplicates_removed} duplicate URL(s). "
                f"Scraping {len(unique_urls)} unique URLs instead of {len(urls)}."
            )

    async def run(self):
        """
        Extracts the content from the links
        """
        contents = await asyncio.gather(
            *(self.extract_data_from_url(url, self.session) for url in self.urls)
        )

        res = [content for content in contents if content["raw_content"] is not None]
        return res

    def _check_pkg(self, scrapper_name: str) -> None:
        """
        Checks and ensures required Python packages are available for scrapers that need
        dependencies beyond requirements.txt. When adding a new scraper to the repo, update `pkg_map`
        with its required information and call check_pkg() during initialization.
        """
        pkg_map = {
            "tavily_extract": {
                "package_installation_name": "tavily-python",
                "import_name": "tavily",
            },
            "firecrawl": {
                "package_installation_name": "firecrawl-py",
                "import_name": "firecrawl",
            },
        }
        pkg = pkg_map[scrapper_name]
        if not importlib.util.find_spec(pkg["import_name"]):
            pkg_inst_name = pkg["package_installation_name"]
            init(autoreset=True)
            print(Fore.YELLOW + f"{pkg_inst_name} not found. Attempting to install...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg_inst_name]
                )
                importlib.invalidate_caches()
                print(Fore.GREEN + f"{pkg_inst_name} installed successfully.")
            except subprocess.CalledProcessError:
                raise ImportError(
                    Fore.RED
                    + f"Unable to install {pkg_inst_name}. Please install manually with "
                    f"`pip install -U {pkg_inst_name}`"
                )

    async def extract_data_from_url(self, link, session):
        """
        Extracts the data from the link with logging
        """
        async with self.worker_pool.throttle():
            try:
                Scraper = self.get_scraper(link)
                scraper = Scraper(link, session)

                # Get scraper name
                scraper_name = scraper.__class__.__name__
                self.logger.info(f"\n=== Using {scraper_name} ===")

                # Get content
                if hasattr(scraper, "scrape_async"):
                    content, image_urls, title = await scraper.scrape_async()
                else:
                    (
                        content,
                        image_urls,
                        title,
                    ) = await asyncio.get_running_loop().run_in_executor(
                        self.worker_pool.executor, scraper.scrape
                    )

                if len(content) < 100:
                    self.logger.warning(f"Content too short or empty for {link}")
                    return {
                        "url": link,
                        "raw_content": None,
                        "image_urls": [],
                        "title": title,
                    }

                # Log results
                self.logger.info(f"\nTitle: {title}")
                self.logger.info(
                    f"Content length: {len(content) if content else 0} characters"
                )
                self.logger.info(f"Number of images: {len(image_urls)}")
                self.logger.info(f"URL: {link}")
                self.logger.info("=" * 50)

                if not content or len(content) < 100:
                    self.logger.warning(f"Content too short or empty for {link}")
                    return {
                        "url": link,
                        "raw_content": None,
                        "image_urls": [],
                        "title": title,
                    }

                if _looks_like_unextracted_pdf(content) and Scraper is not PyMuPDFScraper:
                    self.logger.warning(
                        f"{link} looks like unextracted PDF binary via {scraper_name} "
                        f"(no .pdf suffix, so get_scraper() didn't route it to "
                        f"PyMuPDFScraper) -- retrying with PyMuPDFScraper"
                    )
                    retried = await self._retry_as_pdf(link, session)
                    if retried is not None:
                        return retried
                    self.logger.warning(f"PyMuPDFScraper retry also failed for {link}")
                    return {
                        "url": link,
                        "raw_content": None,
                        "image_urls": [],
                        "title": title,
                    }

                return {
                    "url": link,
                    "raw_content": content,
                    "image_urls": image_urls,
                    "title": title,
                }

            except Exception as e:
                self.logger.error(f"Error processing {link}: {str(e)}")
                return {"url": link, "raw_content": None, "image_urls": [], "title": ""}

    async def _retry_as_pdf(self, link, session):
        """Re-fetch link with PyMuPDFScraper after the scraper get_scraper()
        originally picked returned unextracted PDF binary.

        Returns the normal extract_data_from_url result dict on success, or
        None if the retry also failed to produce usable content (so the
        caller falls back to treating this as an ordinary fetch failure
        instead of passing binary through).
        """
        scraper = PyMuPDFScraper(link, session)
        content, image_urls, title = await asyncio.get_running_loop().run_in_executor(
            self.worker_pool.executor, scraper.scrape
        )
        if not content or len(content) < 100:
            return None
        self.logger.info(f"PyMuPDFScraper retry recovered {len(content)} characters for {link}")
        return {
            "url": link,
            "raw_content": content,
            "image_urls": image_urls,
            "title": title,
        }

    def get_scraper(self, link):
        """
        The function `get_scraper` determines the appropriate scraper class based on the provided link
        or a default scraper if none matches.

        Args:
          link: The `get_scraper` method takes a `link` parameter which is a URL link to a webpage or a
        PDF file. Based on the type of content the link points to, the method determines the appropriate
        scraper class to use for extracting data from that content.

        Returns:
          The `get_scraper` method returns the scraper class based on the provided link. The method
        checks the link to determine the appropriate scraper class to use based on predefined mappings
        in the `SCRAPER_CLASSES` dictionary. If the link ends with ".pdf", it selects the
        `PyMuPDFScraper` class. If the link contains "arxiv.org", it selects the `ArxivScraper
        """

        SCRAPER_CLASSES = {
            "pdf": PyMuPDFScraper,
            "arxiv": ArxivScraper,
            "bs": BeautifulSoupScraper,
            "web_base_loader": WebBaseLoaderScraper,
            "browser": BrowserScraper,
            "nodriver": NoDriverScraper,
            "tavily_extract": TavilyExtract,
            "firecrawl": FireCrawl,
        }

        scraper_key = None

        # Inspect only the path component so query strings / fragments don't
        # hide the extension (e.g. signed CDN/S3 links like "…/doc.pdf?sig=…").
        # Match case-insensitively because ".PDF" is a perfectly valid suffix.
        path = urlparse(link).path
        if path.lower().endswith(".pdf"):
            scraper_key = "pdf"
        elif "arxiv.org" in link:
            scraper_key = "arxiv"
        else:
            scraper_key = self.scraper

        scraper_class = SCRAPER_CLASSES.get(scraper_key)
        if scraper_class is None:
            raise Exception("Scraper not found.")

        return scraper_class
