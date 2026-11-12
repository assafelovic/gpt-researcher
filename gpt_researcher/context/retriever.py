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
    pages: Optional[List[Any]] = None

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        if not self.pages:
            return []

        docs = []
        for page in self.pages:
            if not isinstance(page, dict):
                continue
            title = page.get("title") or ""
            source = page.get("source") or page.get("url") or ""
            raw_content = page.get("raw_content") or ""
            docs.append(
                Document(
                    # ``raw_content`` may be explicitly None (the scraper sets it to
                    # None for pages that failed to scrape), and slicing None raises
                    # TypeError. Coerce to a string before truncating.
                    page_content=str(raw_content)[:_MAX_CONTENT_CHARS],
                    metadata={
                        "title": str(title),
                        "source": str(source),
                    },
                )
            )

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