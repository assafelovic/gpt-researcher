import asyncio
import os

from langchain_community.document_loaders import (
    PyMuPDFLoader, 
    TextLoader, 
    UnstructuredCSVLoader, 
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader, 
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader
)


class DocumentLoader:

    def __init__(self, path):
        self.path = path

    async def load(self) -> list:
        tasks = []
        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                file_name, file_extension_with_dot = os.path.splitext(file_path)
                file_extension = file_extension_with_dot.strip(".")
                tasks.append(self._load_document(file_path, file_extension))

        docs = []
        for pages in await asyncio.gather(*tasks):
            for page in pages:
                if page.page_content:
                    docs.append({
                        "raw_content": page.page_content,
                        "url": os.path.basename(page.metadata['source'])
                    })
                    
        if not docs:
            raise ValueError("🤷 Failed to load any documents!")

        return docs

    async def _load_document(self, file_path: str, file_extension: str) -> list:
        try:
            loader_dict = {
                "pdf": PyMuPDFLoader(file_path),
                "txt": TextLoader(file_path),
                "doc": UnstructuredWordDocumentLoader(file_path),
                "docx": UnstructuredWordDocumentLoader(file_path),
                "pptx": UnstructuredPowerPointLoader(file_path),
                "csv": UnstructuredCSVLoader(file_path, mode="elements"),
                "xls": UnstructuredExcelLoader(file_path, mode="elements"),
                "xlsx": UnstructuredExcelLoader(file_path, mode="elements"),
                "md": UnstructuredMarkdownLoader(file_path)
            }

            loader = loader_dict.get(file_extension, None)
            if loader:
                data = loader.load()
                return data

        except Exception as e:
            print(f"Failed to load document : {file_path}")
            print(e)
            return []
