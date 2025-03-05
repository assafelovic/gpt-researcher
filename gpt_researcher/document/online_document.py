from __future__ import annotations

import os
import tempfile

from typing import TYPE_CHECKING, Any

import aiohttp

from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredCSVLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

logger: logging.Logger = get_formatted_logger(__name__)


class OnlineDocumentLoader:
    def __init__(
        self,
        urls: list[str],
    ):
        self.urls: list[str] = urls

    async def load(self) -> list[dict[str, str]]:
        docs: list[dict[str, str]] = []
        for url in self.urls:
            pages: list[dict[str, str]] = await self._download_and_process(url)
            for page in pages:
                if not page.get("page_content"):
                    continue

                docs.append(
                    {
                        "raw_content": page.get("page_content") or "",
                        "url": page.get("source") or "",
                    }
                )

        if not docs:
            raise ValueError("🤷 Failed to load any documents!")

        return docs

    async def _download_and_process(
        self,
        url: str,
    ) -> list[dict[str, str]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to download {url}: HTTP {response.status}")
                        return []

                    content: bytes = await response.read()
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=self._get_extension(url)
                    ) as tmp_file:
                        tmp_file.write(content)
                        tmp_file_path = tmp_file.name

                    return await self._load_document(
                        tmp_file_path, self._get_extension(url).strip(".")
                    )
        except aiohttp.ClientError as e:
            logger.exception(f"Failed to process {url}: {e.__class__.__name__}: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error processing {url}: {e.__class__.__name__}: {e}")
            return []

    async def _load_document(
        self,
        file_path: str,
        file_extension: str,
    ) -> list[dict[str, str]]:
        ret_data: list[dict[str, str]] = []
        try:
            loader_dict: dict[str, Any] = {
                "pdf": PyMuPDFLoader(file_path),
                "txt": TextLoader(file_path),
                "doc": UnstructuredWordDocumentLoader(file_path),
                "docx": UnstructuredWordDocumentLoader(file_path),
                "pptx": UnstructuredPowerPointLoader(file_path),
                "csv": UnstructuredCSVLoader(file_path, mode="elements"),
                "xls": UnstructuredExcelLoader(file_path, mode="elements"),
                "xlsx": UnstructuredExcelLoader(file_path, mode="elements"),
                "md": UnstructuredMarkdownLoader(file_path),
            }

            loader: Any = loader_dict.get(file_extension, None)
            if loader:
                ret_data = loader.load()

        except Exception as e:
            logger.exception(f"Failed to load document : {file_path} : {e.__class__.__name__}: {e}")
        finally:
            os.remove(file_path)  # 删除临时文件

        return ret_data

    @staticmethod
    def _get_extension(url: str) -> str:
        return os.path.splitext(url.split("?")[0])[1]
