import importlib.util
import unittest
from pathlib import Path

from langchain_core.documents import Document

module_path = (
    Path(__file__).resolve().parents[1]
    / "gpt_researcher"
    / "document"
    / "langchain_document.py"
)
spec = importlib.util.spec_from_file_location("langchain_document", module_path)
langchain_document = importlib.util.module_from_spec(spec)
spec.loader.exec_module(langchain_document)
LangChainDocumentLoader = langchain_document.LangChainDocumentLoader


class TestLangChainDocumentLoader(unittest.IsolatedAsyncioTestCase):
    async def test_load_falls_back_to_standard_source_metadata(self):
        document = Document(
            page_content="Document content",
            metadata={"source": "document.pdf"},
        )

        loaded_documents = await LangChainDocumentLoader([document]).load()

        self.assertEqual(
            loaded_documents,
            [{"raw_content": "Document content", "url": "document.pdf"}],
        )

    async def test_load_prefers_requested_metadata_field(self):
        document = Document(
            page_content="Document content",
            metadata={"title": "Document title", "source": "document.pdf"},
        )

        loaded_documents = await LangChainDocumentLoader([document]).load()

        self.assertEqual(
            loaded_documents,
            [{"raw_content": "Document content", "url": "Document title"}],
        )


if __name__ == "__main__":
    unittest.main()
