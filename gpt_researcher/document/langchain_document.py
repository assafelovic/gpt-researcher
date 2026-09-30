import asyncio
import os

from langchain_core.documents import Document
from typing import List, Dict


# Supports the base Document class from langchain
# - https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/documents/base.py
class LangChainDocumentLoader:

    def __init__(self, documents: List[Document]):
        self.documents = documents

    async def load(self, metadata_source_index="title") -> List[Dict[str, str]]:
        # Mirror the sibling ``DocumentLoader.load()`` hardening:
        # ``self.documents`` is user-supplied (LangChainDocuments report source),
        # so a single malformed row — None, a dict from a JSON payload, or a
        # document with ``metadata=None`` — must not abort the entire load and
        # drop every other document already collected. Skip rows that aren't
        # Document-shaped, default ``None`` / missing metadata to ``{}``, and
        # drop rows without usable ``page_content`` so downstream string
        # operations don't see ``None``.
        docs: List[Dict[str, str]] = []
        for document in self.documents:
            if not hasattr(document, "page_content"):
                continue

            meta = getattr(document, "metadata", None)
            if not isinstance(meta, dict):
                meta = {}

            page_content = getattr(document, "page_content", None)
            if not page_content:
                continue

            docs.append(
                {
                    "raw_content": str(page_content),
                    "url": meta.get(metadata_source_index, "") or "",
                }
            )
        return docs
