"""SearchApi must apply query_domains and report failed requests."""

import importlib.util
import logging
import pathlib
import urllib.parse
from unittest.mock import MagicMock, patch

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "retrievers"
    / "searchapi"
    / "searchapi.py"
)
_spec = importlib.util.spec_from_file_location("_searchapi_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SearchApiSearch = _mod.SearchApiSearch


def _response(status=200, payload=None, text=""):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload or {"organic_results": []}
    response.text = text
    return response


def _sent_query(mock_get):
    url = mock_get.call_args.args[0]
    return urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["q"][0]


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
def test_query_domains_become_site_clauses():
    with patch.object(_mod.requests, "get") as mock_get:
        mock_get.return_value = _response()
        SearchApiSearch("solar output", query_domains=["nrel.gov", "iea.org"]).search()
        assert _sent_query(mock_get) == "(site:nrel.gov OR site:iea.org) solar output"


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
def test_query_is_unchanged_without_domains():
    with patch.object(_mod.requests, "get") as mock_get:
        mock_get.return_value = _response()
        SearchApiSearch("solar output").search()
        assert _sent_query(mock_get) == "solar output"


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
def test_failed_request_is_logged_and_returns_empty(caplog):
    with patch.object(_mod.requests, "get") as mock_get:
        mock_get.return_value = _response(status=401, text="invalid api key")
        with caplog.at_level(logging.WARNING):
            assert SearchApiSearch("solar output").search() == []
        assert "401" in caplog.text and "invalid api key" in caplog.text


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
def test_query_domains_filters_empty_whitespace_and_non_strings():
    with patch.object(_mod.requests, "get") as mock_get:
        mock_get.return_value = _response()
        SearchApiSearch(
            "solar output",
            query_domains=["", "  ", "nrel.gov", None, 123, "iea.org"],
        ).search()
        assert _sent_query(mock_get) == "(site:nrel.gov OR site:iea.org) solar output"


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
def test_query_domains_all_empty_retains_base_query():
    with patch.object(_mod.requests, "get") as mock_get:
        mock_get.return_value = _response()
        SearchApiSearch("solar output", query_domains=["", "  ", None]).search()
        assert _sent_query(mock_get) == "solar output"


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
def test_search_non_positive_max_results_returns_empty_without_request():
    with patch.object(_mod.requests, "get") as mock_get:
        retriever = SearchApiSearch("solar output")
        assert retriever.search(max_results=0) == []
        assert retriever.search(max_results=-5) == []
        mock_get.assert_not_called()


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
def test_search_bounds_results_to_max_results():
    with patch.object(_mod.requests, "get") as mock_get:
        payload = {
            "organic_results": [
                {"title": f"Title {i}", "link": f"https://example.com/{i}", "snippet": f"Body {i}"}
                for i in range(10)
            ]
        }
        mock_get.return_value = _response(payload=payload)
        results = SearchApiSearch("solar output").search(max_results=3)
        assert len(results) == 3
        assert [r["href"] for r in results] == [
            "https://example.com/0",
            "https://example.com/1",
            "https://example.com/2",
        ]
