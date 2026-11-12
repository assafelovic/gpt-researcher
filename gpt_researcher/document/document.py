import asyncio
import os
from typing import List, Union
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredCSVLoader,
UnstructuredEPubLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader
)
from langchain_community.document_loaders import BSHTMLLoader


def detect_utf8(file_path: str) -> str | None:
    """Return "utf-8-sig" if the file decodes as UTF-8, else None.

    TextLoader and BSHTMLLoader otherwise open files with the locale encoding,
    which on Windows is a code page such as cp1252 that rejects or garbles
    UTF-8. Non-UTF-8 files keep that default; "utf-8-sig" also drops a BOM.
    """
    with open(file_path, "rb") as f:
        try:
            f.read().decode("utf-8")
        except UnicodeDecodeError:
            return None
    return "utf-8-sig"


class DocumentLoader:

    def __init__(self, path: Union[str, List[str]]):
        self.path = path

    async def load(self) -> list:
        tasks = []

        def add_file(file_path_str: str):
            filename = os.path.basename(file_path_str)
            _, ext_with_dot = os.path.splitext(filename)
            file_extension = ext_with_dot.strip(".").lower()
            tasks.append(self._load_document(file_path_str, file_extension))

        def add_path(p: Union[str, bytes, os.PathLike]):
            p_str = os.fspath(p) if not isinstance(p, bytes) else os.fsdecode(p)
            if os.path.isfile(p_str):
                add_file(p_str)
            elif os.path.isdir(p_str):
                for root, _, files in os.walk(p_str):
                    for file in files:
                        add_file(os.path.join(root, file))

        if isinstance(self.path, list):
            for item in self.path:
                add_path(item)
        elif isinstance(self.path, (str, bytes, os.PathLike)):
            add_path(self.path)
        else:
            raise ValueError("Invalid type for path. Expected str, bytes, os.PathLike, or list thereof.")

        docs = []
        for pages in await asyncio.gather(*tasks):
            for page in pages:
                if page.page_content:
                    # Loaders occasionally omit metadata["source"] (custom loaders,
                    # some HTML partitions). Prefer source, then fall back to path.
                    meta = getattr(page, "metadata", None) or {}
                    source = meta.get("source") or meta.get("file_path") or ""
                    url = os.path.basename(source) if source else ""
                    docs.append({
                        "raw_content": page.page_content,
                        "url": url,
                    })
                    
        if not docs:
            raise ValueError("🤷 Failed to load any documents!")

        return docs

    async def _load_document(self, file_path: str, file_extension: str) -> list:
        ret_data = []
        try:
            encoding = detect_utf8(file_path) if file_extension in ("txt", "html", "htm") else None
            loader_dict = {
                "pdf": PyMuPDFLoader(file_path),
"epub": UnstructuredEPubLoader(file_path),
                "txt": TextLoader(file_path, encoding=encoding),
                "doc": UnstructuredWordDocumentLoader(file_path),
                "docx": UnstructuredWordDocumentLoader(file_path),
                "pptx": UnstructuredPowerPointLoader(file_path),
                "csv": UnstructuredCSVLoader(file_path, mode="elements"),
                "xls": UnstructuredExcelLoader(file_path, mode="elements"),
                "xlsx": UnstructuredExcelLoader(file_path, mode="elements"),
                "md": UnstructuredMarkdownLoader(file_path),
                "html": BSHTMLLoader(file_path, open_encoding=encoding),
                "htm": BSHTMLLoader(file_path, open_encoding=encoding)
            }

            loader = loader_dict.get(file_extension, None)
            if loader:
                try:
                    ret_data = loader.load()
                except Exception as e:
                    print(
                        f"Failed to load {file_extension or 'unknown'} document: {file_path}"
                    )
                    print(e)

        except Exception as e:
            print(f"Failed to load document : {file_path}")
            print(e)

        return ret_data
