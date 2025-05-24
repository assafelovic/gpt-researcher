from __future__ import annotations

import arxiv
import requests

from langchain.schema import Document
from langchain_community.retrievers import ArxivRetriever


class ArxivScraper:

    def __init__(
        self,
        link: str,
        session: requests.Session | None = None,
        arxiv_search: arxiv.Client | None = None,
        arxiv_exceptions: list[Exception] | None = None,
        load_max_docs: int | None = None,
        doc_content_chars_max: int | None = None,
    ):
        self.link: str = link
        self.session: requests.Session | None = session
        self.arxiv_search: arxiv.Client | None = arxiv_search
        self.arxiv_exceptions: list[Exception] | None = arxiv_exceptions
        self.load_max_docs: int | None = load_max_docs
        self.doc_content_chars_max: int | None = doc_content_chars_max

    def scrape(self) -> str:
        """The function scrapes relevant documents from Arxiv based on a given link and returns the content of the first document.

        Returns:
            The code is returning the page content of the first document retrieved by the ArxivRetriever for a given query extracted from the link.
        """
        query: str = self.link.split("/")[-1]
        retriever: ArxivRetriever = ArxivRetriever(
            arxiv_search=self.arxiv_search,
            arxiv_exceptions=self.arxiv_exceptions,
            load_max_docs=self.load_max_docs,
            doc_content_chars_max=self.doc_content_chars_max,
        )
        docs: list[Document] = retriever.invoke(query)
        return docs[0].page_content
