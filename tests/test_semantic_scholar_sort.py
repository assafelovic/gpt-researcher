"""Regression test for Semantic Scholar sort-criterion casing.

``VALID_SORT_CRITERIA`` holds the API's exact camelCase values
(``citationCount``, ``publicationDate``), and ``__init__`` asserts the
incoming value is one of them. It then stored ``sort.lower()``, corrupting
``citationCount`` -> ``citationcount`` before it was sent as the ``sort``
query parameter. The Semantic Scholar API expects the camelCase form.
"""

from gpt_researcher.retrievers.semantic_scholar.semantic_scholar import (
    SemanticScholarSearch,
)


def test_camelcase_sort_preserved():
    s = SemanticScholarSearch("anything", sort="citationCount")
    assert s.sort == "citationCount"


def test_publication_date_sort_preserved():
    s = SemanticScholarSearch("anything", sort="publicationDate")
    assert s.sort == "publicationDate"


def test_relevance_default_preserved():
    s = SemanticScholarSearch("anything")
    assert s.sort == "relevance"


def test_stored_sort_is_a_valid_api_value():
    # Whatever is stored must round-trip as an accepted API criterion.
    s = SemanticScholarSearch("anything", sort="citationCount")
    assert s.sort in SemanticScholarSearch.VALID_SORT_CRITERIA
