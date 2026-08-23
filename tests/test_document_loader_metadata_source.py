"""DocumentLoader must tolerate pages without metadata['source']."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "document" / "document.py"


def _load():
    # Prevent gpt_researcher package __init__ from loading: load module via path.
    pkg = types.ModuleType("gpt_researcher")
    pkg.__path__ = [str(ROOT / "gpt_researcher")]
    sys.modules.setdefault("gpt_researcher", pkg)
    doc_pkg = types.ModuleType("gpt_researcher.document")
    doc_pkg.__path__ = [str(ROOT / "gpt_researcher" / "document")]
    sys.modules["gpt_researcher.document"] = doc_pkg

    # Stub heavy langchain loaders referenced at import time.
    lcc = types.ModuleType("langchain_community")
    lcc_loaders = types.ModuleType("langchain_community.document_loaders")
    for name in (
        "PyMuPDFLoader",
        "TextLoader",
        "UnstructuredCSVLoader",
        "UnstructuredExcelLoader",
        "UnstructuredMarkdownLoader",
        "UnstructuredPowerPointLoader",
        "UnstructuredWordDocumentLoader",
        "BSHTMLLoader",
    ):
        setattr(lcc_loaders, name, object)
    sys.modules["langchain_community"] = lcc
    sys.modules["langchain_community.document_loaders"] = lcc_loaders

    for key in list(sys.modules):
        if key.endswith("document_doc_testmod"):
            sys.modules.pop(key)

    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.document.document_doc_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_missing_source_uses_empty_url(tmp_path: Path):
    path = tmp_path.joinpath("notes.txt")
    path.write_text("hello", encoding="utf-8")
    mod = _load()
    loader = mod.DocumentLoader(str(tmp_path))

    async def fake_load_document(file_path, file_extension):
        return [
            SimpleNamespace(page_content="body", metadata={}),
            SimpleNamespace(page_content="with", metadata={"source": str(path)}),
        ]

    async def run():
        with patch.object(loader, "_load_document", side_effect=fake_load_document):
            return await loader.load()

    docs = asyncio.run(run())
    assert any(d["raw_content"] == "body" and d["url"] == "" for d in docs)
    assert any(d["raw_content"] == "with" and d["url"] == "notes.txt" for d in docs)
