import os
from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

# Maximum characters of raw_content to embed per document.
# Large documents (e.g. scraped PDFs) can exceed embedding API token limits
# (e.g. OpenAI's 300 000 token-per-request cap) when all chunks are sent at once.
# Defaults to 50 000 chars (~12 500 tokens); override with MAX_CONTENT_CHARS env var.
_MAX_CONTENT_CHARS = int(os.environ.get("MAX_CONTENT_CHARS", 50000))


class SearchAPIRetriever(BaseRetriever):
    """Search API retriever."""
    pages: List[Dict] = []

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:

        docs = [
            Document(
                page_content=page.get("raw_content", "")[:_MAX_CONTENT_CHARS],
                metadata={
                    "title": page.get("title", ""),
                    "source": page.get("url", ""),
                },
            )
            for page in self.pages
        ]

        return docs

class SectionRetriever(BaseRetriever):
    """
    SectionRetriever:
    This class is used to retrieve sections while avoiding redundant subtopics.
    """
    sections: List[Dict] = []
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
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:

        docs = [
            Document(
                page_content=page.get("written_content", ""),
                metadata={
                    "section_title": page.get("section_title", ""),
                },
            )
            for page in self.sections  # Changed 'self.pages' to 'self.sections'
        ]

        return docs