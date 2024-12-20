from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import requests

from . import (
    ArxivScraper,
    BeautifulSoupScraper,
    PyMuPDFScraper,
    WebBaseLoaderScraper,
    BrowserScraper
)


class Scraper:
    """
    Scraper class to extract the content from the links
    """

    def __init__(self, sources, user_agent, scraper):
        """
        Initialize the Scraper class.
        Args:
            sources: List of source URLs to scrape
        """
        self.sources = sources
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.scraper = scraper

    def run(self):
        """
        Extracts the content from the sources
        """
        partial_extract = partial(self.extract_data_from_source, session=self.session)
        with ThreadPoolExecutor(max_workers=20) as executor:
            contents = executor.map(partial_extract, self.sources)
        res = [content for content in contents if content["raw_content"] is not None]
        return res

    def extract_data_from_source(self, source, session):
        """
        Extracts the data from the source
        """
        try:
            Scraper = self.get_scraper(source)
            scraper = Scraper(source, session)
            content, image_urls, title = scraper.scrape()

            if len(content) < 100:
                return {"source": source, "raw_content": None, "image_urls": [], "title": ""}
            
            return {"source": source, "raw_content": content, "image_urls": image_urls, "title": title}
        except Exception as e:
            return {"source": source, "raw_content": None, "image_urls": [], "title": ""}

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
