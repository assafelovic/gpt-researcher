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

# Known anti-bot/challenge-page markers, case-insensitive substring match.
# These pages return HTTP 200 with real (often large) HTML bodies, so
# neither an exception nor the short-content check below catches them --
# without this, a block/challenge page is ingested as if it were the
# article's real content. Not exhaustive; add more as new blockers are
# observed in practice.
_BLOCK_PAGE_MARKERS = (
    "anubis uses a proof-of-work scheme",  # HAL and other Anubis-fronted sites
    "making sure you're not a bot",
    "checking your browser before accessing",
    "enable javascript and cookies to continue",
    "temporarily unavailable",  # ResearchGate's specific wording
    "please verify you are a human",
    "attention required! | cloudflare",
    "sorry, you have been blocked",
    "just a moment...",
)

# Word-list/vocab dumps (plain lists of unrelated words, no prose) scrape
# cleanly and can dominate a report's context, since they lexically match
# almost any query. They have essentially zero sentence-ending punctuation
# relative to their size, unlike any real prose (even dense technical
# writing has a period every ~100-200 characters). Size alone isn't used as
# a signal -- long legitimate documents exist -- only the near-total absence
# of sentence structure combined with real size is checked, to keep the
# false-positive rate on real content low.
_MIN_LENGTH_FOR_WORDLIST_CHECK = 200_000
_MAX_SENTENCE_DENSITY = 1 / 5000  # at most 1 sentence-ending mark per 5000 chars


def _looks_like_block_page(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _BLOCK_PAGE_MARKERS)


def _looks_like_word_list(text: str) -> bool:
    if len(text) < _MIN_LENGTH_FOR_WORDLIST_CHECK:
        return False
    sentence_endings = text.count(".") + text.count("!") + text.count("?")
    return (sentence_endings / len(text)) < _MAX_SENTENCE_DENSITY


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

                if _looks_like_block_page(content):
                    self.logger.warning(
                        f"Anti-bot/challenge page detected for {link}, treating as fetch failure"
                    )
                    return {
                        "url": link,
                        "raw_content": None,
                        "image_urls": [],
                        "title": title,
                    }

                if _looks_like_word_list(content):
                    self.logger.warning(
                        f"Word-list-like content detected for {link}, treating as fetch failure"
                    )
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
