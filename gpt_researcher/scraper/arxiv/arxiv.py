from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableConfig

from gpt_researcher.utils.schemas import BaseScraper

if TYPE_CHECKING:
    from typing_extensions import Literal


class ArxivRetriever(BaseRetriever):
    def __init__(
        self,
        load_max_docs: int,
        doc_content_chars_max: int | None,
    ) -> None:
        self.load_max_docs: int = load_max_docs
        self.doc_content_chars_max: int | None = doc_content_chars_max

    def invoke(
        self,
        input: str,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> list[Document]:
        if not self.doc_content_chars_max:
            raise ValueError("doc_content_chars_max must be provided")
        return super().invoke(input=input, config=config, **kwargs)

    def _get_relevant_documents(self, query: str) -> list[Document]:
        return []


class ArxivScraper(BaseScraper):
    MODULE_NAME: Literal["arxiv"] = "arxiv"

    def scrape(self) -> str:
        """Scrapes relevant documents from Arxiv based on a given link

        Returns:
            The content of the first document retrieved by the ArxivRetriever
        """
        query = self.link.split("/")[-1]
        retriever = ArxivRetriever(
            load_max_docs=2,
            doc_content_chars_max=None,
        )
        docs: list[Document] = retriever.invoke(input=query)
        return docs[0].page_content
