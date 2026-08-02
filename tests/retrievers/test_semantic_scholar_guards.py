"""Guards for Semantic Scholar openAccessPdf / payload shapes."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.semantic_scholar.semantic_scholar import (
    SemanticScholarSearch,
)


def _search_with_payload(payload):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = payload
    with patch(
        "gpt_researcher.retrievers.semantic_scholar.semantic_scholar.requests.get",
        return_value=mock_resp,
    ):
        return SemanticScholarSearch("test query").search(max_results=5)


def test_open_access_pdf_as_string_url():
    out = _search_with_payload(
        {
            "data": [
                {
                    "title": "Paper",
                    "abstract": "Abs",
                    "isOpenAccess": True,
                    "openAccessPdf": "https://example.com/p.pdf",
                }
            ]
        }
    )
    assert out == [
        {
            "title": "Paper",
            "href": "https://example.com/p.pdf",
            "body": "Abs",
        }
    ]


def test_open_access_pdf_object_url():
    out = _search_with_payload(
        {
            "data": [
                {
                    "title": "Paper",
                    "abstract": "Abs",
                    "isOpenAccess": True,
                    "openAccessPdf": {"url": "https://example.com/o.pdf"},
                }
            ]
        }
    )
    assert out[0]["href"] == "https://example.com/o.pdf"


def test_skips_null_open_access_and_non_dict_rows():
    out = _search_with_payload(
        {
            "data": [
                None,
                "bad",
                {
                    "title": "Closed",
                    "isOpenAccess": False,
                    "openAccessPdf": {"url": "https://x"},
                },
                {
                    "title": "OA no pdf",
                    "isOpenAccess": True,
                    "openAccessPdf": None,
                },
            ]
        }
    )
    assert out == []


def test_non_dict_json_returns_empty():
    assert _search_with_payload([]) == []


def test_sort_preserves_camel_case():
    s = SemanticScholarSearch("q", sort="citationCount")
    assert s.sort == "citationCount"
