from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import extract_title, get_relevant_images
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    from langchain_core.documents import Document
    from requests import Session

logger: logging.Logger = get_formatted_logger(__name__)


class WebBaseLoaderScraper:
    def __init__(
        self,
        link: str,
        session: Session | None = None,
        *args: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        self.link: str = link
        self.session: Session = session or requests.Session()
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs


    def scrape(self) -> tuple:
        try:
            from langchain_community.document_loaders import WebBaseLoader

            loader = WebBaseLoader(self.link)
            loader.requests_kwargs = {"verify": False}
            docs: list[Document] = loader.load()
            content: str = ""

            for doc in docs:
                content += doc.page_content

            response: requests.Response = self.session.get(self.link)
            soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
            image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title: str | None = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            logger.exception(f"Error! : {e.__class__.__name__}: {e}")
            return "", [], ""
