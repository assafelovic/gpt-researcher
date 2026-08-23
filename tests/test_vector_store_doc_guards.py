"""VectorStoreWrapper must skip bad document rows."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "vector_store" / "vector_store.py"


def _load():
    # stub langchain pieces imported at module level
    lc_docs = types.ModuleType("langchain_core.documents")
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}
    lc_docs.Document = Document
    sys.modules["langchain_core"] = types.ModuleType("langchain_core")
    sys.modules["langchain_core.documents"] = lc_docs

    lc_vs = types.ModuleType("langchain_community.vectorstores")
    class VectorStore:
        pass
    lc_vs.VectorStore = VectorStore
    sys.modules["langchain_community"] = types.ModuleType("langchain_community")
    sys.modules["langchain_community.vectorstores"] = lc_vs

    splitter_mod = types.ModuleType("langchain_text_splitters")
    class RecursiveCharacterTextSplitter:
        def __init__(self, **k):
            pass
        def split_documents(self, docs):
            return docs
    splitter_mod.RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter
    sys.modules["langchain_text_splitters"] = splitter_mod

    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.vector_store.vector_store", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class VectorStoreDocGuards(unittest.TestCase):
    def test_skips_non_dict_and_none_content(self):
        mod = _load()
        wrap = mod.VectorStoreWrapper(MagicMock())
        docs = wrap._create_langchain_documents(
            [
                None,
                "x",
                {"url": "https://a", "raw_content": None},
                {"url": "https://b", "raw_content": "hello"},
                {"raw_content": "no-url"},
            ]
        )
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].page_content, "hello")
        self.assertEqual(docs[0].metadata["source"], "https://b")
        self.assertEqual(docs[1].metadata["source"], "")


if __name__ == "__main__":
    unittest.main()
