from __future__ import annotations

import os
from typing import Any

class TavilyExtract:
import requests

from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import extract_title, get_relevant_images


    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
    ):
        self.link: str = link
        self.session: requests.Session | None = session
        from tavily import TavilyClient

        self.tavily_client: TavilyClient = TavilyClient(api_key=self.get_api_key())

    def get_api_key(self) -> str:
        """Gets the Tavily API key.

        Returns:
            Api key (str)
        """
        try:
            api_key: str = os.environ["TAVILY_API_KEY"]
        except KeyError:
            raise Exception("Tavily API key not found. Please set the TAVILY_API_KEY environment variable.")
        return api_key

    def scrape(self) -> tuple[str, list[dict[str, Any]], str]:
        try:
            response: dict = self.tavily_client.extract(urls=self.link)
            if response["failed_results"]:
                return "", [], ""

            # Parse the HTML content of the response to create a BeautifulSoup object for the utility functions
            response_bs: requests.Response = self.session.get(self.link, timeout=4)
            soup: BeautifulSoup = BeautifulSoup(response_bs.content, "lxml", from_encoding=response_bs.encoding)

            # Since only a single link is provided to tavily_client, the results will contain only one entry.
            content: str = response["results"][0]["raw_content"]

            # Get relevant images using the utility function
            image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title: str = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            print(f"Error! : {e.__class__.__name__}: {e}")
            return "", [], ""
