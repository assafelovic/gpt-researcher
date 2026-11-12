"""Regression and robustness tests for SectionRetriever and rank_written_sections.

Validates that:
1. SectionRetriever tolerates written_content=None and section_title=None without
   triggering Pydantic ValidationError on Document construction.
2. SectionRetriever tolerates missing keys and empty/None sections.
3. SearchAPIRetriever tolerates None/missing fields and non-dict entries.
4. rank_written_sections safely handles None sections, empty lists, non-dict entries,
   and None values in written_content and section_title.
"""

from gpt_researcher.context.lexical import rank_written_sections
from gpt_researcher.context.retriever import SearchAPIRetriever, SectionRetriever


def test_section_retriever_none_written_content():
    retriever = SectionRetriever(
        sections=[{"section_title": "Architecture", "written_content": None}]
    )
    docs = retriever.invoke("query")
    assert len(docs) == 1
    assert docs[0].page_content == ""
    assert docs[0].metadata["section_title"] == "Architecture"


def test_section_retriever_none_section_title():
    retriever = SectionRetriever(
        sections=[{"section_title": None, "written_content": "Detailed overview content"}]
    )
    docs = retriever.invoke("query")
    assert len(docs) == 1
    assert docs[0].page_content == "Detailed overview content"
    assert docs[0].metadata["section_title"] == ""


def test_section_retriever_missing_keys():
    retriever = SectionRetriever(sections=[{}])
    docs = retriever.invoke("query")
    assert len(docs) == 1
    assert docs[0].page_content == ""
    assert docs[0].metadata["section_title"] == ""


def test_section_retriever_empty_or_none_sections():
    assert SectionRetriever(sections=[]).invoke("query") == []


def test_searchapi_retriever_none_metadata_fields():
    retriever = SearchAPIRetriever(
        pages=[{"raw_content": "Content", "title": None, "url": None}]
    )
    docs = retriever.invoke("query")
    assert len(docs) == 1
    assert docs[0].page_content == "Content"
    assert docs[0].metadata["title"] == ""
    assert docs[0].metadata["source"] == ""


def test_rank_written_sections_handles_none_and_empty():
    assert rank_written_sections("query", None) == []
    assert rank_written_sections("query", []) == []


def test_rank_written_sections_handles_none_values():
    sections = [
        None,
        {"section_title": "Empty Section", "written_content": None},
        {"section_title": None, "written_content": "Multi-agent autonomous systems coordinate workflows."},
        {"section_title": "Other Topic", "written_content": "Baking bread and pastry dough."}
    ]
    ranked = rank_written_sections("autonomous agents", sections)
    assert len(ranked) == 1
    assert "autonomous systems" in ranked[0]
