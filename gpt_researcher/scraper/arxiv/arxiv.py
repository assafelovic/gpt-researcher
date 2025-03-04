from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_community.retrievers import ArxivRetriever

if TYPE_CHECKING:
    pass


class ArxivScraper:
    def __init__(
        self,
        link: str,
        session: Any | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        self.link: str = link
        self.session: Any | None = session

    def scrape(self) -> tuple[str, list[Any], Any]:
        """
        The function scrapes relevant documents from Arxiv based on a given link and returns the content
        of the first document.

        Returns:
            The code is returning the page content of the first document retrieved by the ArxivRetriever
            for a given query extracted from the link.
        """
        query: str = self.link.split("/")[-1]
        retriever: ArxivRetriever = ArxivRetriever(
            load_max_docs=2,
            doc_content_chars_max=None,
            arxiv_search=None,
            arxiv_exceptions=None,
        )
        docs: list[Any] = retriever.invoke(query)
        # returns content, image_urls, title
        return docs[0].page_content, [], docs[0].metadata["Title"]
