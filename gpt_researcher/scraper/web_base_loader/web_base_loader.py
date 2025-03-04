from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import requests
from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import extract_title, get_relevant_images

if TYPE_CHECKING:
    from requests import Session

logger = logging.getLogger(__name__)


class WebBaseLoaderScraper:
    def __init__(
        self,
        link: str,
        session: Session | None = None,
        *_: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        self.link: str = link
        self.session: Session = session or requests.Session()

    def scrape(self) -> tuple:
        try:
            from langchain_community.document_loaders import WebBaseLoader

            loader = WebBaseLoader(self.link)
            loader.requests_kwargs = {"verify": False}
            docs = loader.load()
            content = ""

            for doc in docs:
                content += doc.page_content

            response = self.session.get(self.link)
            soup = BeautifulSoup(response.content, "html.parser")
            image_urls = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            logger.exception(f"Error! : {e.__class__.__name__}: {e}")
            return "", [], ""
