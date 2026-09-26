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


def test_request_uses_timeout():
    response = _resp({"data": []})
    with patch("requests.get", return_value=response) as mock_get:
        SemanticScholarSearch("q").search()

    _, kwargs = mock_get.call_args
    assert kwargs["timeout"] == 10


def test_malformed_json_returns_empty():
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.side_effect = ValueError("invalid json")

    with patch("requests.get", return_value=response):
        assert SemanticScholarSearch("q").search() == []
