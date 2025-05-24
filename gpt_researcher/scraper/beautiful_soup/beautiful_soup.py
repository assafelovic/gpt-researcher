from __future__ import annotations

from typing import Any

import requests

from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import extract_title, get_relevant_images


    def __init__(self, link, session=None):
    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
    ):
        self.link: str = link
        self.session: requests.Session | None = session
        self.timeout: int = 3

    def scrape(self) -> tuple[str, list[dict[str, Any]], str] | tuple[str, list[dict[str, Any]], str]:
        try:
            response: requests.Response = self.session.get(self.link, timeout=self.timeout)
            soup: BeautifulSoup = BeautifulSoup(response.content, "lxml", from_encoding=response.encoding)

            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            raw_content: str = self.get_content_from_url(soup)
            lines: list[str] = [line.strip() for line in raw_content.splitlines()]
            chunks: list[str] = [phrase.strip() for line in lines for phrase in line.split("  ")]
            content: str = "\n".join(chunk for chunk in chunks if chunk)

            image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title: str = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""

    def get_content_from_url(self, soup: BeautifulSoup) -> str:
        """Get the relevant text from the soup with improved filtering.

        Args:
            soup: The BeautifulSoup object to extract text from.

        Returns:
            The relevant text from the soup with improved filtering.
        """
        text_elements: list[str] = []
        tags: list[str] = ["h1", "h2", "h3", "h4", "h5", "p", "li", "div", "span"]

        for element in soup.find_all(tags):
            # Skip empty elements
            if not str(element.text).strip():
                continue

            # Skip elements with very short text (likely buttons or links)
            if len(str(element.text).split()) < 3:
                continue

            # Check if the element is likely to be navigation or a menu
            parent_classes: list[str] = str(element.parent.get("class", [])).split()
            if any(cls in ["nav", "menu", "sidebar", "footer"] for cls in parent_classes):
                continue

            # Remove excess whitespace and join lines
            cleaned_text: str = " ".join(str(element.text).split())

            # Add the cleaned text to our list of elements
            text_elements.append(cleaned_text)

        # Join all text elements with newlines
        return "\n\n".join(text_elements)
