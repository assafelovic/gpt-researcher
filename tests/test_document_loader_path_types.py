import asyncio
import os
from pathlib import Path
import pytest

from gpt_researcher.document.document import DocumentLoader


def test_document_loader_single_file_str(tmp_path):
    doc_path = tmp_path / "sample.txt"
    doc_path.write_text("Hello from single file string", encoding="utf-8")

    docs = asyncio.run(DocumentLoader(str(doc_path)).load())
    assert len(docs) == 1
    assert docs[0]["raw_content"] == "Hello from single file string"
    assert docs[0]["url"] == "sample.txt"


def test_document_loader_single_file_path(tmp_path):
    doc_path = tmp_path / "research.txt"
    doc_path.write_text("Autonomous AI agent research", encoding="utf-8")

    docs = asyncio.run(DocumentLoader(doc_path).load())
    assert len(docs) == 1
    assert docs[0]["raw_content"] == "Autonomous AI agent research"
    assert docs[0]["url"] == "research.txt"


def test_document_loader_directory_str_and_path(tmp_path):
    (tmp_path / "a.txt").write_text("content a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("content b", encoding="utf-8")

    docs_str = asyncio.run(DocumentLoader(str(tmp_path)).load())
    assert len(docs_str) == 2
    assert {d["url"]: d["raw_content"] for d in docs_str} == {
        "a.txt": "content a",
        "b.txt": "content b",
    }

    docs_path = asyncio.run(DocumentLoader(tmp_path).load())
    assert len(docs_path) == 2
    assert {d["url"]: d["raw_content"] for d in docs_path} == {
        "a.txt": "content a",
        "b.txt": "content b",
    }


def test_document_loader_list_of_mixed_paths(tmp_path):
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    f1.write_text("content 1", encoding="utf-8")
    f2.write_text("content 2", encoding="utf-8")

    docs = asyncio.run(DocumentLoader([str(f1), f2]).load())
    assert len(docs) == 2
    assert {d["url"]: d["raw_content"] for d in docs} == {
        "file1.txt": "content 1",
        "file2.txt": "content 2",
    }


def test_document_loader_invalid_type():
    with pytest.raises(ValueError, match="Invalid type for path"):
        asyncio.run(DocumentLoader(12345).load())


def test_document_loader_empty_or_missing_raises(tmp_path):
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="Failed to load any documents"):
        asyncio.run(DocumentLoader(str(empty_dir)).load())
