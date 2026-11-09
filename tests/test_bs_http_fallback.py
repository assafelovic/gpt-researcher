"""Bounded HTTP fallback behavior for the BeautifulSoup scraper."""

from unittest.mock import MagicMock, patch

import pytest

from gpt_researcher.scraper.beautiful_soup.beautiful_soup import (
    MAX_CONTENT_BYTES,
    TRANSPARENT_RESEARCH_USER_AGENT,
    BeautifulSoupScraper,
)


class Response:
    def __init__(self, status_code):
        self.status_code = status_code
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.content = b"<html><body>usable source content</body></html>"
        self.encoding = "utf-8"


def test_success_uses_configured_session_identity_once():
    session = MagicMock()
    response = Response(200)
    session.get.return_value = response

    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is response
    session.get.assert_called_once_with(
        "https://example.com/source", timeout=10,
    )
    assert scraper.failure_reason is None


def test_403_retries_once_with_transparent_identity_and_recovers():
    session = MagicMock()
    recovered = Response(200)
    session.get.side_effect = [Response(403), recovered]

    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is recovered
    assert session.get.call_count == 2
    assert session.get.call_args_list[0].kwargs == {"timeout": 10}
    assert session.get.call_args_list[1].kwargs == {
        "timeout": 10,
        "headers": {"User-Agent": TRANSPARENT_RESEARCH_USER_AGENT},
    }
    assert scraper.failure_reason is None


def test_persistent_403_stops_after_one_fallback_and_preserves_reason():
    session = MagicMock()
    session.get.side_effect = [Response(403), Response(403)]
    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is None
    assert session.get.call_count == 2
    assert session.get.call_args_list[1].kwargs == {
        "timeout": 10,
        "headers": {"User-Agent": TRANSPARENT_RESEARCH_USER_AGENT},
    }
    assert scraper.failure_reason == "HTTP_403"


def test_404_is_not_retried_and_preserves_reason():
    session = MagicMock()
    session.get.return_value = Response(404)
    scraper = BeautifulSoupScraper("https://example.com/missing", session)

    assert scraper._fetch() is None
    assert session.get.call_count == 1
    assert scraper.failure_reason == "HTTP_404"


@pytest.mark.parametrize("status_code", [429, 500, 502, 503, 504])
@patch("gpt_researcher.scraper.beautiful_soup.beautiful_soup.time.sleep")
def test_transient_status_retry_behavior_is_unchanged(sleep, status_code):
    session = MagicMock()
    recovered = Response(200)
    session.get.side_effect = [Response(status_code), recovered]
    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is recovered
    assert session.get.call_count == 2
    assert session.get.call_args_list[1].kwargs == {"timeout": 10}
    sleep.assert_called_once_with(1)


@patch("gpt_researcher.scraper.beautiful_soup.beautiful_soup.time.sleep")
def test_request_exception_retry_behavior_is_unchanged(sleep):
    session = MagicMock()
    recovered = Response(200)
    session.get.side_effect = [OSError("connection reset"), recovered]
    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is recovered
    assert session.get.call_count == 2
    assert session.get.call_args_list[1].kwargs == {"timeout": 10}
    sleep.assert_called_once_with(1)


@patch("gpt_researcher.scraper.beautiful_soup.beautiful_soup.time.sleep")
def test_two_request_exceptions_stop_after_existing_retry_limit(sleep):
    session = MagicMock()
    session.get.side_effect = [
        OSError("connection reset"),
        TimeoutError("request timed out"),
    ]
    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is None
    assert session.get.call_count == 2
    assert scraper.failure_reason is None
    sleep.assert_called_once_with(1)


def test_403_fallback_does_not_add_a_third_retry_for_transient_status():
    session = MagicMock()
    session.get.side_effect = [Response(403), Response(503)]
    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is None
    assert session.get.call_count == 2
    assert scraper.failure_reason == "HTTP_503"


@patch("gpt_researcher.scraper.beautiful_soup.beautiful_soup.time.sleep")
def test_transient_retry_followed_by_403_does_not_add_a_third_request(sleep):
    session = MagicMock()
    session.get.side_effect = [Response(503), Response(403)]
    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is None
    assert session.get.call_count == 2
    assert scraper.failure_reason == "HTTP_403"
    sleep.assert_called_once_with(1)


def test_oversized_response_behavior_is_unchanged():
    session = MagicMock()
    response = Response(200)
    response.headers["Content-Length"] = str(MAX_CONTENT_BYTES + 1)
    session.get.return_value = response
    scraper = BeautifulSoupScraper("https://example.com/source", session)

    assert scraper._fetch() is None
    assert session.get.call_count == 1
    assert scraper.failure_reason is None
