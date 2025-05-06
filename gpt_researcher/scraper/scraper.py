from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from colorama import Fore, init

import requests
import subprocess
import sys
import importlib

from . import (
    ArxivScraper,
    BeautifulSoupScraper,
    PyMuPDFScraper,
    WebBaseLoaderScraper,
    BrowserScraper,
    TavilyExtract
)


class Scraper:
    """
    Scraper class to extract the content from the links
    """

    def __init__(self, urls, user_agent, scraper):
        """
        Initialize the Scraper class.
        Args:
            urls:
        """
        self.urls = urls
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.scraper = scraper
        if self.scraper == "tavily_extract":
            self._check_pkg(self.scraper)

    def run(self):
        """
        Extracts the content from the links
        """
        partial_extract = partial(self.extract_data_from_url, session=self.session)
        with ThreadPoolExecutor(max_workers=20) as executor:
            contents = executor.map(partial_extract, self.urls)
        res = [content for content in contents if content["raw_content"] is not None]
        return res

    def _check_pkg(self, scrapper_name : str) -> None:
        """
        Checks and ensures required Python packages are available for scrapers that need
        dependencies beyond requirements.txt. When adding a new scraper to the repo, update `pkg_map`
        with its required information and call check_pkg() during initialization.
        """
        pkg_map = {
            "tavily_extract": {"package_installation_name": "tavily-python",
                               "import_name": "tavily"},
        }
        pkg = pkg_map[scrapper_name]
        if not importlib.util.find_spec(pkg["import_name"]):
            pkg_inst_name = pkg["package_installation_name"]
            init(autoreset=True)
            print(Fore.YELLOW + f"{pkg_inst_name} not found. Attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_inst_name])
                print(Fore.GREEN + f"{pkg_inst_name} installed successfully.")
            except subprocess.CalledProcessError:
                raise ImportError(
                    Fore.RED + f"Unable to install {pkg_inst_name}. Please install manually with "
                               f"`pip install -U {pkg_inst_name}`"
                )

    def extract_data_from_url(self, link, session):
        """
        Extracts the data from the link
        """
        try:
            Scraper = self.get_scraper(link)
            scraper = Scraper(link, session)
            content, image_urls, title = scraper.scrape()

            if len(content) < 100:
                return {"url": link, "raw_content": None, "image_urls": [], "title": ""}
            
            return {"url": link, "raw_content": content, "image_urls": image_urls, "title": title}
        except Exception as e:
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
            "tavily_extract": TavilyExtract
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
