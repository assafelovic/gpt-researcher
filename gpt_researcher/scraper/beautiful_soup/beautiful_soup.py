from __future__ import annotations

import logging
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from gpt_researcher.scraper.utils import extract_title, get_relevant_images

logger = logging.getLogger(__name__)


class BeautifulSoupScraper:
    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
    ):
        self.link: str = link
        self.session: requests.Session | None = session

    def scrape(
        self,
        timeout: int = 4,
        features: str = "lxml",
    ) -> tuple[str, list[dict[str, Any]], str | None]:
        """Scrapes content from a webpage.

        Will make a GET request to the specified link, parse the HTML with BeautifulSoup,
        remove script and style elements, and extract the cleaned text content.

        Returns:
            tuple: A tuple containing the cleaned content as a string, a list of image URLs, and the page title.
        """
        try:
            assert self.session is not None, "Session is not initialized"
            response = self.session.get(self.link, timeout=timeout)
            soup = BeautifulSoup(
                response.content,
                features,
                from_encoding=response.encoding,
            )

            for script_or_style in soup(["script", "style"]):
                assert isinstance(script_or_style, Tag)
                script_or_style.extract()

            raw_content: str = self.get_content_from_url(soup)
            lines: list[str] = [line.strip() for line in raw_content.splitlines()]
            chunks: list[str] = [phrase.strip() for line in lines for phrase in line.split("  ")]
            content: str = "\n".join(chunk for chunk in chunks if chunk)

            image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title: str | None = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            logger.exception(
                f"Unexpected error occurred while scraping: {e.__class__.__name__}: {e}"
            )
            return "", [], ""

    def get_content_from_url(
        self,
        soup: BeautifulSoup,
    ) -> str:
        """Get the relevant text from the soup with improved filtering."""
        text_elements: list[str] = []
        tags: list[str] = ["h1", "h2", "h3", "h4", "h5", "p", "li", "div", "span"]

        for element in soup.find_all(tags):
            assert isinstance(element, Tag)
            # Skip empty elements
            if not element.text.strip():
                continue

            # Skip elements with very short text (likely buttons or links)
            if len(element.text.split()) < 3:
                continue

            if not element.parent:
                continue

            # Check if the element is likely to be navigation or a menu
            parent_classes: list[str] | str | None = element.parent.get("class", [])
            if parent_classes and any(
                cls in ["nav", "menu", "sidebar", "footer"] for cls in parent_classes
            ):
                continue

            # Remove excess whitespace and join lines
            cleaned_text: str = " ".join(element.text.split())

            # Add the cleaned text to our list of elements
            text_elements.append(cleaned_text)

        # Join all text elements with newlines
        return "\n\n".join(text_elements)
