import os
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_community.document_loaders.powerpoint import UnstructuredPowerPointLoader
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
from langchain_community.document_loaders.csv_loader import UnstructuredCSVLoader
from langchain_community.document_loaders.pdf import UnstructuredPDFLoader


class DocumentLoader:

    def __init__(self, path):
        self.path = path

    def load(self) -> list:
        docs = []

        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                file_name, file_extension = os.path.splitext(file_path)
                print(f"Loading file : {file_path}")
                print(f"File extension : {file_extension}")
                docs.extend(self._load_document(file_path, file_extension))

        return docs

    def _load_document(self, file_path: str, file_extension: str) -> list:
        try:

            # PDF
            if file_extension == "pdf":
                data = self._load_pdf(file_path)

            # WORD
            elif file_extension == "doc" or file_extension == "docx":
                data = self._load_docx(file_path)

            # PPT
            elif file_extension == "pptx":
                data = self._load_pptx(file_path)

            # TXT
            elif file_extension == "txt":
                data = self._load_txt(file_path)

            # CSV
            elif file_extension == "csv":
                data = self._load_csv(file_path)

            elif file_extension == "xls" or file_extension == "xlsx":
                data = self._load_excel(file_path)

            else:
                data = []

            return data

        except Exception as e:
            print(e)
            return []

    def _load_pdf(self, file_path: str) -> list:
        loader = UnstructuredPDFLoader(file_path)
        docs = loader.load()

        print("length of docs : ", len(docs))

        return docs

    def _load_docx(self, file_path: str) -> list:
        loader = UnstructuredWordDocumentLoader(file_path)
        docs = loader.load()

        return docs

    def _load_pptx(self, file_path: str) -> list:
        loader = UnstructuredPowerPointLoader(file_path)
        docs = loader.load()

        return docs

    def _load_txt(self, file_path: str) -> list:
        loader = TextLoader(file_path)
        docs = loader.load()

        return docs

    def _load_excel(self, file_path: str) -> list:
        loader = UnstructuredExcelLoader(file_path, mode="elements")
        docs = loader.load()

        return docs

    def _load_csv(self, file_path: str) -> list:
        loader = UnstructuredCSVLoader(file_path, mode="elements")
        docs = loader.load()

        return docs
