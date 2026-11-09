"""LangChainDocumentLoader.load() must tolerate malformed rows.

``self.documents`` is user-supplied via the LangChainDocuments report source, so
the loader has to survive a single malformed row without dropping every other
document already collected. Mirrors the hardening in ``DocumentLoader.load()``
sibling — getattr-with-default + isinstance guard.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from langchain_core.documents import Document

from gpt_researcher.document.langchain_document import LangChainDocumentLoader


def _loader(docs):
    # bypass __init__ side-effects if any; current __init__ is trivial
    return LangChainDocumentLoader(docs)


async def _load(docs):
    return await _loader(docs).load()


def test_normal_documents_pass_through():
    docs = [
        Document(page_content="hello", metadata={"title": "http://a.example"}),
        Document(page_content="world", metadata={"title": "http://b.example"}),
    ]
    assert await _load(docs) == [
        {"raw_content": "hello", "url": "http://a.example"},
        {"raw_content": "world", "url": "http://b.example"},
    ]


def test_missing_metadata_key_yields_empty_url():
    docs = [Document(page_content="no title", metadata={})]
    assert await _load(docs) == [{"raw_content": "no title", "url": ""}]


def test_metadata_none_is_treated_as_empty_dict():
    # Realistic path: a custom Document subclass or a legacy loader omits
    # metadata. The default LangChain Document model rejects None at
    # construction, so simulate with a duck-typed object. Previously this
    # crashed with ``AttributeError: 'NoneType' object has no attribute 'get'``
    # and dropped every other document already collected; now the row is
    # included with an empty URL — same behaviour as the sibling
    # ``DocumentLoader.load()``, which also tolerates ``metadata=None``.
    bad = SimpleNamespace(page_content="orphan", metadata=None)
    good = Document(page_content="kept", metadata={"title": "http://kept"})
    out = await _load([bad, good])
    assert out == [
        {"raw_content": "orphan", "url": ""},
        {"raw_content": "kept", "url": "http://kept"},
    ]


def test_non_document_rows_are_skipped():
    # A caller that serialised through JSON and forgot to reconstruct the
    # Document object ends up with a dict in the list. Real bug: previously
    # AttributeError on .page_content aborted the entire load.
    rows = [
        Document(page_content="real", metadata={"title": "http://real"}),
        {"page_content": "fake", "metadata": {"title": "http://fake"}},
        "string row",
        None,
        Document(page_content="another", metadata={"title": "http://another"}),
    ]
    assert await _load(rows) == [
        {"raw_content": "real", "url": "http://real"},
        {"raw_content": "another", "url": "http://another"},
    ]


def test_empty_list_returns_empty():
    assert await _load([]) == []


def test_empty_page_content_is_skipped():
    rows = [
        Document(page_content="", metadata={"title": "http://empty"}),
        Document(page_content="kept", metadata={"title": "http://kept"}),
    ]
    assert await _load(rows) == [{"raw_content": "kept", "url": "http://kept"}]


def test_custom_metadata_source_index_is_respected():
    docs = [Document(page_content="x", metadata={"source": "http://src", "title": "http://title"})]
    out = await _load(docs)
    assert out[0]["url"] == "http://title"
    # and now with a key actually present
    docs2 = [Document(page_content="x", metadata={"source": "http://src"})]
    out2 = await _loader(docs2).load(metadata_source_index="source")
    assert out2[0]["url"] == "http://src"


def test_magic_mock_with_attributes_works():
    # MagicMock auto-creates page_content/metadata attrs, so it passes the
    # hasattr gate. This sanity check documents the contract — a row that
    # quacks like a Document must not be filtered.
    mock_row = MagicMock(spec=["page_content", "metadata"])
    mock_row.page_content = "mock"
    mock_row.metadata = {"title": "http://mock"}
    assert await _load([mock_row]) == [{"raw_content": "mock", "url": "http://mock"}]