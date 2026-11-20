"""UTF-8 .txt and .html documents must load intact whatever the locale is.

TextLoader and BSHTMLLoader open files with the locale encoding unless given
one. On Windows before Python 3.15 that is the ANSI code page (cp1252 on most
installs), so UTF-8 documents raised UnicodeDecodeError and were skipped, or
came back garbled.
The ``cp1252_locale`` fixture recreates that default on any OS.
"""

import asyncio
import builtins

import langchain_community.document_loaders.html_bs as lc_html
import langchain_community.document_loaders.text as lc_text
import pytest

from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.document.online_document import OnlineDocumentLoader


@pytest.fixture
def cp1252_locale(monkeypatch):
    def open_with_cp1252_default(file, mode="r", *args, encoding=None, **kwargs):
        if encoding is None and "b" not in mode:
            encoding = "cp1252"
        return builtins.open(file, mode, *args, encoding=encoding, **kwargs)

    # Shadow the builtin open() inside the two loader modules only.
    for module in (lc_text, lc_html):
        monkeypatch.setattr(module, "open", open_with_cp1252_default, raising=False)


def test_utf8_documents_load_intact(tmp_path, cp1252_locale):
    expected = {
        "ja.txt": "これは日本語のテキストです。",
        "fr.txt": "Résumé: “café” — naïve",
        "ru.txt": "Привет, мир",
        "ja.html": "東京は日本の首都です。",
    }
    for name in ("ja.txt", "fr.txt", "ru.txt"):
        tmp_path.joinpath(name).write_text(expected[name], encoding="utf-8")
    tmp_path.joinpath("ja.html").write_text(
        f"<html><body><p>{expected['ja.html']}</p></body></html>", encoding="utf-8"
    )

    docs = asyncio.run(DocumentLoader(str(tmp_path)).load())

    assert {d["url"]: d["raw_content"] for d in docs} == expected


def test_utf8_bom_is_dropped(tmp_path, cp1252_locale):
    tmp_path.joinpath("notes.txt").write_text("naïve", encoding="utf-8-sig")

    docs = asyncio.run(DocumentLoader(str(tmp_path)).load())

    assert docs == [{"raw_content": "naïve", "url": "notes.txt"}]


def test_non_utf8_text_keeps_the_locale_encoding(tmp_path, cp1252_locale):
    tmp_path.joinpath("legacy.txt").write_bytes("Café crème, déjà vu".encode("cp1252"))

    docs = asyncio.run(DocumentLoader(str(tmp_path)).load())

    assert docs == [{"raw_content": "Café crème, déjà vu", "url": "legacy.txt"}]


def test_downloaded_utf8_txt_loads_intact(tmp_path, cp1252_locale):
    path = tmp_path.joinpath("download.txt")
    path.write_text("这是一个中文研究文档，包含一些内容。", encoding="utf-8")

    pages = asyncio.run(OnlineDocumentLoader([])._load_document(str(path), "txt"))

    assert [page.page_content for page in pages] == ["这是一个中文研究文档，包含一些内容。"]
