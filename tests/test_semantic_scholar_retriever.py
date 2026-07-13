"""Guards for Semantic Scholar malformed payloads / openAccessPdf shapes."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.semantic_scholar.semantic_scholar import (
    SemanticScholarSearch,
)


def _resp(payload):
    r = MagicMock()
    r.raise_for_status = MagicMock()
    r.json.return_value = payload
    return r


def test_open_access_pdf_none_does_not_crash():
    payload = {
        "data": [
            {
                "title": "A",
                "isOpenAccess": True,
                "openAccessPdf": None,
                "abstract": "x",
            }
        ]
    }
    with patch("requests.get", return_value=_resp(payload)):
        out = SemanticScholarSearch("q").search()
    assert out == []


def test_open_access_pdf_string_skipped():
    payload = {
        "data": [
            {
                "title": "A",
                "isOpenAccess": True,
                "openAccessPdf": "https://not-a-dict",
                "abstract": "x",
            }
        ]
    }
    with patch("requests.get", return_value=_resp(payload)):
        assert SemanticScholarSearch("q").search() == []


def test_happy_path_url():
    payload = {
        "data": [
            {
                "title": "Paper",
                "isOpenAccess": True,
                "openAccessPdf": {"url": "https://pdf.example/p.pdf"},
                "abstract": "abs",
            }
        ]
    }
    with patch("requests.get", return_value=_resp(payload)):
        out = SemanticScholarSearch("q").search()
    assert out == [
        {"title": "Paper", "href": "https://pdf.example/p.pdf", "body": "abs"}
    ]
