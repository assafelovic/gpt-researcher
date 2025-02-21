from __future__ import annotations

import asyncio
import logging
import os

from pathlib import Path
from typing import Any, Coroutine, Sequence

from langchain_community.document_loaders import (
    BSHTMLLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredCSVLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)

logger: logging.Logger = logging.getLogger(__name__)


def _normalize_path(path: os.PathLike | str) -> Path:
    return Path(os.path.expandvars(os.path.normpath(path))).absolute()


class DocumentLoader:
    def __init__(
        self,
        path: os.PathLike | str | Sequence[os.PathLike | str],
    ):
        self.path: Path | list[Path] = _normalize_path(path) if isinstance(path, (os.PathLike, str)) else [_normalize_path(p) for p in path]

    async def load(self) -> list[dict[str, Any]]:
        def _load_doc(file: os.PathLike | str) -> None:
            file_path: Path = Path(file)
            if file_path.exists() and file_path.is_file():
                file_extension_with_dot: str = file_path.suffix
                file_extension: str = file_extension_with_dot[1:].casefold()
                doc: Coroutine[Any, Any, list[dict[str, Any]]] = self._load_document(str(file_path), file_extension)
                tasks.append(doc)
            else:
                logger.error(f"File '{file_path}' does not exist or is not a file.")

        tasks: list[Coroutine[Any, Any, list[dict[str, Any]]]] = []
        if isinstance(self.path, list):
            for file in self.path:
                _load_doc(file)

        elif isinstance(self.path, (str, os.PathLike)):
            for root, dirs, files in os.walk(self.path):
                for file in files:
                    _load_doc(os.path.join(root, file))
        else:
            raise ValueError(f"Invalid type for argument 'path'. Expected str, os.PathLike, or list, but got `{self.path.__class__.__name__}`.")

        docs: list[dict[str, Any]] = []
        for pages in await asyncio.gather(*tasks):
            for page in pages:
                if not page or not isinstance(page, dict):
                    continue
                page_content: str | None = getattr(page, "page_content", None)
                if not page_content or not page_content.strip():
                    continue
                metadata: dict[str, Any] | None = getattr(page, "metadata", None)
                if not metadata:
                    continue
                source: str | None = metadata.get("source", None)
                if not source or not source.strip():
                    continue
                docs.append(
                    {
                        "raw_content": page_content,
                        "url": os.path.basename(source),
                    }
                )

        if not docs:
            raise ValueError("🤷 Failed to load any documents!")

        return docs

    async def _load_document(
        self,
        file_path: str,
        file_extension: str,
    ) -> list:
        ret_data: list[dict[str, Any]] = []
        try:
            loader_dict: dict[str, Any] = {
                "csv": UnstructuredCSVLoader(file_path, mode="elements"),
                "doc": UnstructuredWordDocumentLoader(file_path),
                "docx": UnstructuredWordDocumentLoader(file_path),
                "htm": BSHTMLLoader(file_path),
                "html": BSHTMLLoader(file_path),
                "md": UnstructuredMarkdownLoader(file_path),
                "pdf": PyMuPDFLoader(file_path),
                "pptx": UnstructuredPowerPointLoader(file_path),
                "txt": TextLoader(file_path),
                "xls": UnstructuredExcelLoader(file_path, mode="elements"),
                "xlsx": UnstructuredExcelLoader(file_path, mode="elements"),
            }

            loader = loader_dict.get(file_extension, None)
            if loader:
                try:
                    ret_data = loader.load()
                except Exception as e:
                    logger.error(f"Failed to load HTML document: '{file_path}'")
                    logger.exception(e)

        except Exception as e:
            logger.error(f"Failed to load document: '{file_path}'")
            logger.exception(e)

        return ret_data
