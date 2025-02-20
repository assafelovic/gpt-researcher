from __future__ import annotations

import importlib
import importlib.util
import logging
import subprocess
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING, Any, Callable

from colorama import Fore, init
from requests import Session

from gpt_researcher.scraper.arxiv.arxiv import ArxivScraper
from gpt_researcher.scraper.beautiful_soup.beautiful_soup import BeautifulSoupScraper
from gpt_researcher.scraper.browser.browser import BrowserScraper
from gpt_researcher.scraper.pymupdf.pymupdf import PyMuPDFScraper
from gpt_researcher.scraper.tavily_extract.tavily_extract import TavilyExtract
from gpt_researcher.scraper.web_base_loader.web_base_loader import WebBaseLoaderScraper

if TYPE_CHECKING:
    from gpt_researcher.utils.schemas import BaseScraper

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(
        self,
        urls: list[str],
        user_agent: str,
        scraper: str,
    ) -> None:
        self.urls: list[str] = urls
        self.session: Session = Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.scraper: str = scraper
        if self.scraper == "tavily_extract":
            self._check_pkg(self.scraper)

    def run(self):
        """Extracts the content from the links."""
        partial_extract: Callable[[str, Session], dict[str, Any]] = partial(
            self.extract_data_from_url,
            session=self.session,
        )
        with ThreadPoolExecutor(max_workers=20) as executor:
            contents: list[dict[str, Any]] = list(executor.map(partial_extract, self.urls))
        res: list[dict[str, Any]] = [
            content for content in contents if content["raw_content"] is not None
        ]
        return res

    def _check_pkg(
        self,
        scrapper_name: str,
    ) -> None:
        pkg_map = {
            "tavily_extract": {
                "package_installation_name": "tavily-python",
                "import_name": "tavily",
            },
        }
        pkg = pkg_map[scrapper_name]
        if not importlib.util.find_spec(pkg["import_name"]):
            pkg_inst_name = pkg["package_installation_name"]
            init(autoreset=True)
            logger.warning(Fore.YELLOW + f"{pkg_inst_name} not found. Attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_inst_name])
                logger.info(Fore.GREEN + f"{pkg_inst_name} installed successfully.")
            except subprocess.CalledProcessError as e:
                raise ImportError(
                    Fore.RED
                    + f"Unable to install {pkg_inst_name}. Please install manually with `pip install -U {pkg_inst_name}`"
                ) from e

    def extract_data_from_url(
        self,
        link: str,
        session: Session,
    ) -> dict[str, Any]:
        """Extracts the data from the link."""
        try:
            scraper_type: type[BaseScraper] = self.get_scraper(link)
            scraper: BaseScraper = scraper_type(link, session, self.scraper)
            content, image_urls, title = scraper.scrape()

            if len(content) < 100:
                return {"url": link, "raw_content": None, "image_urls": [], "title": ""}

            return {"url": link, "raw_content": content, "image_urls": image_urls, "title": title}
        except Exception as e:
            return {"url": link, "raw_content": None, "image_urls": [], "title": ""}

    def get_scraper(
        self,
        link: str,
    ) -> type[BaseScraper]:
        SCRAPER_CLASSES = {
            "pdf": PyMuPDFScraper,
            "arxiv": ArxivScraper,
            "bs": BeautifulSoupScraper,
            "web_base_loader": WebBaseLoaderScraper,
            "browser": BrowserScraper,
            "tavily_extract": TavilyExtract,
        }

        scraper_key = None

        if link.endswith(".pdf"):
            scraper_key = "pdf"
        elif "arxiv.org" in link:
            scraper_key = "arxiv"
        else:
            scraper_key = self.scraper

        scraper_class = SCRAPER_CLASSES.get(scraper_key)
        if scraper_class is None:
            raise Exception("Scraper not found.")

        return scraper_class
