from __future__ import annotations

import asyncio
import importlib
import importlib.util
import logging
import subprocess
import sys

from multiprocessing import cpu_count
from typing import TYPE_CHECKING, Any

from colorama import Fore, init
from requests import Session

from gpt_researcher.scraper import (
    ArxivScraper,
    BeautifulSoupScraper,
    BrowserScraper,
    FireCrawl,
    NoDriverScraper,
    PyMuPDFScraper,
    TavilyExtract,
    WebBaseLoaderScraper,
)
from gpt_researcher.utils.schemas import BaseScraper
from gpt_researcher.utils.workers import WorkerPool

if TYPE_CHECKING:
    from gpt_researcher.utils.schemas import BaseScraper


class Scraper:
    def __init__(
        self,
        urls: list[str],
        user_agent: str,
        scraper: str,
        worker_pool: WorkerPool,
        timeout: int | None = 10,
        max_workers: int | None = None,
    ) -> None:
        """Initialize the Scraper class.

        Args:
            urls (list[str]): The list of URLs to scrape.
            user_agent (str): The user agent to use for the request.
            scraper (str): The scraper to use.
            timeout (int | None): The timeout for the request.
            max_workers (int | None): The maximum number of workers to use.
        """
        self.urls: list[str] = urls
        self.session: Session = Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.scraper: str = scraper
        if self.scraper == "tavily_extract":
            self._check_pkg(self.scraper)
        self.timeout: int = 10 if timeout is None else timeout
        self.max_workers: int = cpu_count() * 2 if max_workers is None else max_workers
        if self.scraper == "firecrawl":
            self._check_pkg(self.scraper)
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.worker_pool: WorkerPool = worker_pool

    async def run(self) -> list[dict[str, Any]]:
        """
        Extracts the content from the links
        """
        contents: list[dict[str, Any]] = await asyncio.gather(
            *(self.extract_data_from_url(url, self.session) for url in self.urls)
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
        pkg_map: dict[str, dict[str, str]] = {
            "tavily_extract": {
                "package_installation_name": "tavily-python",
                "import_name": "tavily",
            },
            "firecrawl": {
                "package_installation_name": "firecrawl-py",
                "import_name": "firecrawl",
            },
        }
        pkg: dict[str, str] = pkg_map[scrapper_name]
        if not importlib.util.find_spec(pkg["import_name"]):
            pkg_inst_name: str = pkg["package_installation_name"]
            init(autoreset=True)
            self.logger.warning(Fore.YELLOW + f"{pkg_inst_name} not found. Attempting to install...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg_inst_name],
                )
                print(Fore.GREEN + f"{pkg_inst_name} installed successfully.")
            except subprocess.CalledProcessError:
                raise ImportError(
                    Fore.RED + f"Unable to install {pkg_inst_name}. Please install manually with "
                    f"`pip install -U {pkg_inst_name}`"
                )
                self.logger.info(Fore.GREEN + f"{pkg_inst_name} installed successfully.")
            except subprocess.CalledProcessError as e:
                raise ImportError(
                    Fore.RED
                    + f"Unable to install {pkg_inst_name}. Please install manually with `pip install -U {pkg_inst_name}`"
                ) from e

    async def extract_data_from_url(
        self,
        link: str,
        session: Session,
    ) -> dict[str, Any]:
        """
        Extracts the data from the link with logging
        """
        async with self.worker_pool.throttle():
            try:
                Scraper: type[BaseScraper] = self.get_scraper(link)
                scraper = Scraper(link, session)

                # Get scraper name
                scraper_name: str = scraper.__class__.__name__
                self.logger.info(f"\n=== Using {scraper_name} ===")

                # Get content
                if hasattr(scraper, "scrape_async"):
                    content, image_urls, title = await scraper.scrape_async()
                else:
                    (
                        content,
                        image_urls,
                        title,
                    ) = await asyncio.get_running_loop().run_in_executor(self.worker_pool.executor, scraper.scrape)

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
                self.logger.info(f"Content length: {len(content) if content else 0} characters")
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

                return {
                    "url": link,
                    "raw_content": content,
                    "image_urls": image_urls,
                    "title": title,
                }

            except Exception as e:
                self.logger.error(f"Error processing {link}: {str(e)}")
                return {"url": link, "raw_content": None, "image_urls": [], "title": ""}

    def get_scraper(
        self,
        link: str,
    ) -> type[BaseScraper]:
        """Gets the scraper type for the link.

        Args:
            link (str): The link to scrape.

        Returns:
            type[BaseScraper]: The scraper type for the link.
        """
        SCRAPER_CLASSES: dict[str, type[BaseScraper]] = {  # type: ignore[var-annotated]
            "arxiv": ArxivScraper,
            "browser": BrowserScraper,
            "bs": BeautifulSoupScraper,
            "firecrawl": FireCrawl,
            "nodriver": NoDriverScraper,
            "pdf": PyMuPDFScraper,
            "tavily_extract": TavilyExtract,
            "web_base_loader": WebBaseLoaderScraper,
        }

        scraper_key: str | None = None

        if link.endswith(".pdf"):
            scraper_key = "pdf"
        elif "arxiv.org" in link:
            scraper_key = "arxiv"
        else:
            scraper_key = self.scraper

        scraper_class: type[BaseScraper] | None = SCRAPER_CLASSES.get(scraper_key)
        if scraper_class is None:
            raise Exception("Scraper not found.")

        return scraper_class
