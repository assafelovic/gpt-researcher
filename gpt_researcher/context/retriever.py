from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever

if TYPE_CHECKING:
    from langchain.callbacks.manager import CallbackManagerForRetrieverRun


class SearchAPIRetriever(BaseRetriever):
    """Search API retriever."""

    pages: ClassVar[list[dict[str, Any]]] = []

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        docs: list[Document] = [
            Document(
                page_content=page.get("raw_content", ""),
                metadata={
                    "title": page.get("title", ""),
                    "source": page.get("url", ""),
                },
            )
            for page in self.pages
        ]

        return docs


class SectionRetriever(BaseRetriever):
    """SectionRetriever:

    This class is used to retrieve sections while avoiding redundant subtopics.
    """

    sections: ClassVar[list[dict[str, Any]]] = []
    """
    sections example:
    [
        {
            "section_title": "Example Title",
            "written_content": "Example content"
        },
        ...
    ]
    """

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        docs: list[Document] = [
            Document(
                page_content=page.get("written_content", ""),
                metadata={
                    "section_title": page.get("section_title", ""),
                },
            )
            for page in self.sections
        ]

        return docs
