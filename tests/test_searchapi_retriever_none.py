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


def test_none_pages_or_default_instantiation():
    retriever_default = SearchAPIRetriever()
    assert retriever_default.invoke("q") == []

    retriever_none = SearchAPIRetriever(pages=None)
    assert retriever_none.invoke("q") == []


def test_none_or_non_dict_elements_in_pages():
    retriever = SearchAPIRetriever(pages=[None, "invalid", {"raw_content": "valid", "title": "t", "url": "u"}])
    docs = retriever.invoke("q")
    assert len(docs) == 1
    assert docs[0].page_content == "valid"


def test_none_title_and_url_coerced_to_empty_strings():
    retriever = SearchAPIRetriever(pages=[{"raw_content": "body", "title": None, "url": None}])
    docs = retriever.invoke("q")
    assert len(docs) == 1
    assert docs[0].metadata["title"] == ""
    assert docs[0].metadata["source"] == ""


def test_source_key_fallback_in_pages():
    retriever = SearchAPIRetriever(pages=[{"raw_content": "body", "title": "t", "source": "https://source.example"}])
    docs = retriever.invoke("q")
    assert len(docs) == 1
    assert docs[0].metadata["source"] == "https://source.example"


def test_select_context_tolerates_none_pages():
    import asyncio

    from gpt_researcher.config import Config
    from gpt_researcher.context.select import select_context

    cfg = Config()
    res_none = asyncio.run(select_context("query", None, cfg))
    assert res_none == ""

    res_malformed = asyncio.run(select_context("query", [None, {"title": None, "url": None, "raw_content": None}], cfg))
    assert isinstance(res_malformed, str)
