from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import clean_soup, extract_title, get_relevant_images, get_text_from_soup
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    import requests

logger: logging.Logger = get_formatted_logger(__name__)


class BeautifulSoupScraper:
    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
        *args: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        self.link: str = link
        self.session: requests.Session | None = session
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

    def scrape(
        self,
        timeout: int = 8,
        features: str = "lxml",
    ) -> tuple[str, list[dict[str, Any]], str | None]:
        """Scrapes content from a webpage.

        Will make a GET request to the specified link, parse the HTML with BeautifulSoup,
        remove script and style elements, and extract the cleaned text content.

        Args:
            timeout (int): The timeout for the GET request.
            features (str): The features to use for parsing the HTML.

        Raises:
            AssertionError: If the session is not initialized.

        Returns:
            tuple: A tuple containing the cleaned content as a string, a list of image URLs, and the page title.
        """
        try:
            assert self.session is not None, "Session is not initialized"
            response: requests.Response = self.session.get(self.link, timeout=timeout)
            soup: BeautifulSoup = BeautifulSoup(
                response.content,
                features,
                from_encoding=response.encoding,
            )

            soup = clean_soup(soup)

            content: str = get_text_from_soup(soup)
            image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)
            title: str | None = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            logger.error(f"Unexpected error occurred while scraping link '{self.link}'! {e.__class__.__name__}: {e}")
            return "", [], ""
