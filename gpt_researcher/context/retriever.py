from __future__ import annotations


from typing import Any

from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever


class SearchAPIRetriever(BaseRetriever):
    """Search API retriever."""

    pages: list[dict[str, Any]] = []

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        """Retrieve relevant documents from the pages.

        Args:
            query (str): The query to retrieve relevant documents from.
            run_manager (CallbackManagerForRetrieverRun): The callback manager for the retriever run.

        Returns:
            list[Document]: The relevant documents.
        """
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

    sections: list[dict[str, Any]] = []
    """Sections example:
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
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        """Retrieve relevant documents from the sections.

        Args:
            query (str): The query to retrieve relevant documents from.
            run_manager (CallbackManagerForRetrieverRun): The callback manager for the retriever run.

        Returns:
            list[Document]: The relevant documents.
        """
        docs: list[Document] = [
            Document(
                page_content=page.get("written_content", ""),
                metadata={
                    "section_title": page.get("section_title", ""),
                },
            )
            for page in self.sections  # Changed 'self.pages' to 'self.sections'
        ]

        return docs
