from __future__ import annotations

import asyncio
import logging
import os

from pathlib import Path
from typing import Any, Coroutine

from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredCSVLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)

logger = logging.getLogger(__name__)


class DocumentLoader:
    def __init__(self, path: os.PathLike | str):
        self.path: Path = Path(os.path.expandvars(os.path.normpath(path))).absolute()

    async def load(self) -> list:
        tasks: list[Coroutine[Any, Any, list]] = []
        for root, _dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                _file_name, file_extension_with_dot = os.path.splitext(file_path)
                file_extension = file_extension_with_dot.strip(".")
                tasks.append(self._load_document(file_path, file_extension))

        docs: list[dict] = []
        for pages in await asyncio.gather(*tasks):
            for page in pages:
                if page.page_content:
                    docs.append(
                        {
                            "raw_content": page.page_content,
                            "url": os.path.basename(page.metadata["source"]),
                        }
                    )

        if not docs:
            raise ValueError("🤷 Failed to load any documents!")

        return docs

    async def _load_document(
        self,
        file_path: os.PathLike | str,
        file_extension: str,
    ) -> list:
        ret_data = []
        path_obj = Path(os.path.expandvars(os.path.normpath(file_path)))
        try:
            loader_dict: dict[str, Any] = {
                "pdf": PyMuPDFLoader(str(path_obj)),
                "txt": TextLoader(str(path_obj)),
                "doc": UnstructuredWordDocumentLoader(str(path_obj)),
                "docx": UnstructuredWordDocumentLoader(str(path_obj)),
                "pptx": UnstructuredPowerPointLoader(str(path_obj)),
                "csv": UnstructuredCSVLoader(str(path_obj), mode="elements"),
                "xls": UnstructuredExcelLoader(str(path_obj), mode="elements"),
                "xlsx": UnstructuredExcelLoader(str(path_obj), mode="elements"),
                "md": UnstructuredMarkdownLoader(str(path_obj)),
            }

            loader: Any = loader_dict.get(file_extension, None)
            if loader:
                ret_data = loader.load()

        except Exception as e:
            logger.error(f"Failed to load document : {file_path}")
            logger.exception(e)

        return ret_data
