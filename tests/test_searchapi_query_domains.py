"""SearchApi must apply query_domains and report failed requests."""

import logging
import urllib.parse
from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.searchapi.searchapi import SearchApiSearch


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
@patch("gpt_researcher.retrievers.searchapi.searchapi.requests.get")
def test_query_domains_become_site_clauses(mock_get):
    mock_get.return_value = _response()
    SearchApiSearch("solar output", query_domains=["nrel.gov", "iea.org"]).search()
    assert _sent_query(mock_get) == "(site:nrel.gov OR site:iea.org) solar output"


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
@patch("gpt_researcher.retrievers.searchapi.searchapi.requests.get")
def test_query_is_unchanged_without_domains(mock_get):
    mock_get.return_value = _response()
    SearchApiSearch("solar output").search()
    assert _sent_query(mock_get) == "solar output"


@patch.dict("os.environ", {"SEARCHAPI_API_KEY": "test"})
@patch("gpt_researcher.retrievers.searchapi.searchapi.requests.get")
def test_failed_request_is_logged_and_returns_empty(mock_get, caplog):
    mock_get.return_value = _response(status=401, text="invalid api key")
    with caplog.at_level(logging.WARNING):
        assert SearchApiSearch("solar output").search() == []
    assert "401" in caplog.text and "invalid api key" in caplog.text
