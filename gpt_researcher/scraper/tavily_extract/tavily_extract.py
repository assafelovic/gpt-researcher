from __future__ import annotations

import logging
import os
from typing import Any

import requests
from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import extract_title, get_relevant_images

logger = logging.getLogger(__name__)


class TavilyExtract:
    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
    ):
        self.link: str = link
        self.session: requests.Session = requests.Session() if session is None else session
        from tavily.tavily import TavilyClient

        self.tavily_client: TavilyClient = TavilyClient(api_key=self.get_api_key())

    def get_api_key(self) -> str:
        try:
            api_key = os.environ["TAVILY_API_KEY"]
        except KeyError:
            raise Exception(
                "Tavily API key not found. Please set the TAVILY_API_KEY environment variable."
            )
        return api_key

    def scrape(self) -> tuple[str, list[str], str]:
        try:
            response: dict[str, Any] = self.tavily_client.extract(urls=self.link)
            if response["failed_results"]:
                return "", [], ""

            # Parse the HTML content of the response to create a BeautifulSoup object for the utility functions
            response_bs = self.session.get(self.link, timeout=4)
            soup = BeautifulSoup(response_bs.content, "lxml", from_encoding=response_bs.encoding)

            # Since only a single link is provided to tavily_client, the results will contain only one entry.
            content = response["results"][0]["raw_content"]
            logger.info(f"Content: {content}")

            # Get relevant images using the utility function
            image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title = extract_title(soup) or ""

            return content, [image["url"] for image in image_urls], title

        except Exception as e:
            logger.exception("Error! : " + str(e))
            return "", [], ""
