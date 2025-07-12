from __future__ import annotations

from typing import Any

import requests

from bs4 import BeautifulSoup
from langchain_core.documents import Document

from gpt_researcher.scraper.utils import extract_title, get_relevant_images

class WebBaseLoaderScraper:
    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
    ):
        self.link: str = link
        self.session: requests.Session | None = session

    def scrape(self) -> tuple[str, list[dict[str, Any]], str]:
        try:
            from langchain_community.document_loaders import WebBaseLoader

            loader: WebBaseLoader = WebBaseLoader(self.link)
            loader.requests_kwargs = {"verify": False}
            docs: list[Document] = loader.load()
            content: str = ""

            for doc in docs:
                content += doc.page_content

            response: requests.Response = self.session.get(self.link)
            soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
            image_urls: list[dict[str, Any]] = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title: str = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            print(f"Error! : {e.__class__.__name__}: {e}")
            return "", [], ""
