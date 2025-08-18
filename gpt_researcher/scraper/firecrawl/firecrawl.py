from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    from requests import Response, Session


class FireCrawl:
    def __init__(
        self,
        link: str,
        session: Session | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        self.link: str = link
        self.session: Session | None = session
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

        from firecrawl import FirecrawlApp
        self.firecrawl: FirecrawlApp = FirecrawlApp(api_key=self.get_api_key(), api_url=self.get_server_url())
        self.logger: logging.Logger = get_formatted_logger(__name__)

    def get_api_key(self) -> str:
        """Gets the FireCrawl API key.

        Returns:
            Api key (str)
        """
        try:
            api_key = os.environ["FIRECRAWL_API_KEY"]
        except KeyError:
            raise Exception("FireCrawl API key not found. Please set the FIRECRAWL_API_KEY environment variable.")
        return api_key

    def get_server_url(self) -> str:
        """Gets the FireCrawl server URL.

        Default to official FireCrawl server ('https://api.firecrawl.dev').

        Returns:
            server url (str)
        """
        try:
            server_url = os.environ["FIRECRAWL_SERVER_URL"]
        except KeyError:
            server_url = "https://api.firecrawl.dev"
        return server_url

def scrape(self) -> tuple[str, list[dict[str, Any]], str]:
    """Extracts content and title from a specified link using the FireCrawl Python SDK.

    Images from the link are extracted using the functions from `gpt_researcher/scraper/utils.py`.

    Returns:
        A tuple containing the extracted content, a list of image URLs, and the title of the webpage specified by the `self.link` attribute.
        It uses the FireCrawl Python SDK to extract and clean content from the webpage. If any exception occurs during the process, an error
        message is logged and an empty result is returned.
    """

    try:
        response = self.firecrawl.scrape_url(url=self.link, formats=["markdown"])

        # Check if the page has been scraped successfully
        if "error" in response:
            self.logger.error(f"Scrape failed! : {response['error']}")
            return "", [], ""
        elif response.get("metadata", {}).get("statusCode") != 200:
            self.logger.error(f"Scrape failed! : {response}")
            return "", [], ""

        # Extract content and title from FireCrawl response (support both formats)
        content = (
            getattr(response, "markdown", None)
            or getattr(getattr(response, "data", {}), "markdown", "")
        )
        title = (
            getattr(getattr(response, "metadata", {}), "get", lambda k, d="": d)("title")
            if hasattr(response, "metadata")
            else response.get("metadata", {}).get("title", "")
        )

        # Parse the HTML content of the response to create a BeautifulSoup object for the utility functions
        assert self.session is not None
        response_bs: Response = self.session.get(self.link, timeout=4)
        soup: BeautifulSoup = BeautifulSoup(response_bs.content, "lxml", from_encoding=response_bs.encoding)

        # Get relevant images using the utility function
        from gpt_researcher.scraper.utils import get_relevant_images
        image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)

        return content, image_urls, title

    except Exception as e:
        self.logger.exception(f"Error! : {e.__class__.__name__}: {e}")
        return "", [], ""

