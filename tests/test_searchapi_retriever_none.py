"""Regression: SearchAPIRetriever must tolerate raw_content=None.

The scraper sets ``raw_content`` to ``None`` for pages that failed to scrape.
Slicing ``None`` raises ``TypeError``, so the retriever must coerce a missing
or None ``raw_content`` to an empty string.
"""

from gpt_researcher.context.retriever import SearchAPIRetriever


def test_none_raw_content_yields_empty_page_content():
    retriever = SearchAPIRetriever(
        pages=[{"raw_content": None, "title": "t", "url": "https://u.example"}]
    )
    docs = retriever.invoke("q")
    assert len(docs) == 1
    assert docs[0].page_content == ""
    assert docs[0].metadata["source"] == "https://u.example"


def test_present_raw_content_is_preserved():
    retriever = SearchAPIRetriever(
        pages=[{"raw_content": "hello world", "title": "t", "url": "u"}]
    )
    docs = retriever.invoke("q")
    assert docs[0].page_content == "hello world"


def test_missing_raw_content_key_yields_empty():
    retriever = SearchAPIRetriever(pages=[{"title": "t", "url": "u"}])
    docs = retriever.invoke("q")
    assert docs[0].page_content == ""
