from __future__ import annotations

import asyncio
import importlib
import importlib.util
import subprocess
import sys

from multiprocessing import cpu_count
from typing import TYPE_CHECKING, Any

from colorama import Fore, init
from requests import Session

from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.config import Config

if TYPE_CHECKING:
    import logging

    from gpt_researcher.scraper.scraper_abc import BaseScraperABC
    from gpt_researcher.utils.workers import WorkerPool


class Scraper:
    def __init__(
        self,
        urls: list[str],
        user_agent: str,
        scraper: str,
        worker_pool: WorkerPool,
        timeout: int | None = None,
        max_workers: int | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize the Scraper class.

        Args:
            urls (list[str]): The list of URLs to scrape.
            user_agent (str): The user agent to use for the request.
            scraper (str): The scraper to use.
            worker_pool (WorkerPool): The worker pool to use.
            timeout (int | None): The timeout for the request. If None, uses config.SCRAPER_TIMEOUT.
            max_workers (int | None): The maximum number of workers to use. If None, uses config.SCRAPER_MAX_WORKERS.
            config (Config | None): The configuration object.
        """
        self.urls: list[str] = urls
        self.session: Session = Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.scraper: str = scraper
        self.config: Config | None = config
        
        if self.scraper == "tavily_extract":
            self._check_pkg(self.scraper)
            
        # Use configuration values if available
        if config is not None:
            self.timeout: int = timeout if timeout is not None else getattr(config, "SCRAPER_TIMEOUT", 10)
            self.max_workers: int = max_workers if max_workers is not None else getattr(config, "SCRAPER_MAX_WORKERS", cpu_count() * 2)
        else:
            self.timeout: int = 10 if timeout is None else timeout
            self.max_workers: int = cpu_count() * 2 if max_workers is None else max_workers
            
        if self.scraper in ["firecrawl", "scrapy"]:
            self._check_pkg(self.scraper)
            
        self.logger: logging.Logger = get_formatted_logger(__name__)
        self.worker_pool: WorkerPool = worker_pool

    async def run(self) -> list[dict[str, Any]]:
        """Extracts the content from the links."""
        contents: list[dict[str, Any]] = await asyncio.gather(
            *(
                self.extract_data_from_url(url, self.session)
                for url in self.urls
            )
        )

        res: list[dict[str, Any]] = [content for content in contents if content["raw_content"] is not None]
        return res

    def _check_pkg(
        self,
        scrapper_name: str,
    ) -> None:
        """Checks and ensures required Python packages are available for scrapers that need dependencies beyond requirements.txt.

        When adding a new scraper to the repo, update `pkg_map`
        with its required information and call check_pkg() during initialization.
        """
        pkg_map = {
            "firecrawl": {
                "pkg_name": "firecrawl",
                "import_name": "firecrawl",
            },
            "tavily_extract": {
                "package_installation_name": "tavily-python",
                "import_name": "tavily",
            },
            "scrapy": {
                "pkg_name": "scrapy",
                "import_name": "scrapy",
            },
        }
        pkg: dict[str, str] = pkg_map[scrapper_name]
        if not importlib.util.find_spec(pkg["import_name"]):
            pkg_inst_name: str = pkg["package_installation_name"]
            init(autoreset=True)
            self.logger.warning(Fore.YELLOW + f"{pkg_inst_name} not found. Attempting to install...")
            try:
                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        pkg_inst_name,
                    ],
                )
                self.logger.info(Fore.GREEN + f"{pkg_inst_name} installed successfully.")
            except subprocess.CalledProcessError:
                raise ImportError(
                    Fore.RED + f"Unable to install {pkg_inst_name}. Please install manually with "
                    f"`pip install -U {pkg_inst_name}`"
                )

    async def extract_data_from_url(
        self,
        link: str,
        session: Session,
    ) -> dict[str, Any]:
        """Extracts the data from the link with logging."""
        async with self.worker_pool.throttle():
            try:
                scraper_cls: type[BaseScraperABC] = self.get_scraper(link)
                scraper = scraper_cls(link, session)  # type: ignore[call-arg]

                # Get scraper name
                scraper_name: str = scraper.__class__.__name__
                self.logger.debug(f"\n=== Using {scraper_name} ===")

                # Get content
                content, image_urls, title = scraper.scrape()

                if len(content) < 100:
                    self.logger.debug(f"Content too short or empty for {link}")
                    return {"url": link, "raw_content": None, "image_urls": [], "title": title}

                # Log results
                self.logger.debug(f"\nTitle: {title}")
                self.logger.debug(f"Content length: {len(content) if content else 0} characters")
                self.logger.debug(f"Number of images: {len(image_urls)}")
                self.logger.debug(f"URL: {link}")
                self.logger.debug("=" * 50)

                if not content or len(content) < 100:
                    self.logger.debug(f"Content too short or empty for {link}")
                    return {"url": link, "raw_content": None, "image_urls": [], "title": title}

                return {
                    "url": link,
                    "raw_content": content,
                    "image_urls": image_urls,
                    "title": title
                }

            except Exception as e:
                self.logger.exception(f"Error processing '{link}'! {e.__class__.__name__}: {e}")
                return {"url": link, "raw_content": None, "image_urls": [], "title": ""}

    def get_scraper(
        self,
        link: str,
    ) -> type[BaseScraperABC]:
        """Gets the scraper type for the link.

        Args:
            link (str): The link to scrape.

        Returns:
            type[BaseScraper]: The scraper type for the link.
        """
        from gpt_researcher.scraper import (
            ArxivScraper,
            BeautifulSoupScraper,
            BrowserScraper,
            FireCrawl,
            NoDriverScraper,
            PyMuPDFScraper,
            TavilyExtract,
            WebBaseLoaderScraper,
            ScrapyScraper,
        )
        SCRAPER_CLASSES: dict[str, type[BaseScraperABC]] = {  # type: ignore[var-annotated]
            "arxiv": ArxivScraper,
            "browser": BrowserScraper,
            "bs": BeautifulSoupScraper,
            "firecrawl": FireCrawl,
            "nodriver": NoDriverScraper,
            "pdf": PyMuPDFScraper,
            "tavily_extract": TavilyExtract,
            "web_base_loader": WebBaseLoaderScraper,
            "scrapy": ScrapyScraper,
        }

        scraper_key: str | None = None

        case_link: str = link.casefold()
        if case_link.endswith(".pdf"):
            scraper_key = "pdf"
        elif "arxiv.org" in case_link:
            scraper_key = "arxiv"
        else:
            scraper_key = self.scraper

        scraper_class: type[BaseScraperABC] | None = SCRAPER_CLASSES.get(scraper_key)  # type: ignore[var-annotated]
        if scraper_class is None:
            raise Exception("Scraper not found.")

        return scraper_class
