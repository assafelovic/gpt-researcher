from __future__ import annotations

from typing import Any

from langchain_community.retrievers import ArxivRetriever


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
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

    def scrape(self) -> tuple[str, list[Any], Any]:
        """Scrape relevant documents from Arxiv based on a given link.

        Returns:
            tuple[str, list[Any], Any]: The content of the first document, an empty list of images, and the title of the first document.
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
