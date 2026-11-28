"""Offline regression tests for bounded streaming reads in BeautifulSoupScraper."""

from unittest.mock import MagicMock

from gpt_researcher.scraper.beautiful_soup import beautiful_soup as bs_mod
from gpt_researcher.scraper.beautiful_soup.beautiful_soup import BeautifulSoupScraper

_BASE = "https://example.com"


class _StreamingResponse:
    def __init__(self, chunks, *, status_code=200, headers=None, encoding="utf-8"):
        self.status_code = status_code
        self.headers = (
            headers
            if headers is not None
            else {"Content-Type": "text/html; charset=utf-8"}
        )
        self.encoding = encoding
        self._chunks = list(chunks)
        self.chunks_yielded = 0
        self.closed = False

    def iter_content(self, chunk_size=65536):
        for chunk in self._chunks:
            self.chunks_yielded += 1
            yield chunk

    def close(self):
        self.closed = True


def test_oversized_content_length_skips_body_read_and_closes_response(monkeypatch):
    monkeypatch.setattr(bs_mod, "MAX_CONTENT_BYTES", 1024)
    response = _StreamingResponse(
        [b"a" * 2048],
        headers={"Content-Type": "text/html", "Content-Length": "2048"},
    )
    session = MagicMock()
    session.get.return_value = response

    content, images, title = BeautifulSoupScraper(f"{_BASE}/huge", session).scrape()

    assert (content, images, title) == ("", [], "")
    assert response.chunks_yielded == 0
    assert response.closed is True
    session.get.assert_called_once_with(f"{_BASE}/huge", timeout=10, stream=True)


def test_chunked_response_exceeding_cap_aborts_stream_early(monkeypatch):
    monkeypatch.setattr(bs_mod, "MAX_CONTENT_BYTES", 100)
    # 10 chunks of 40 bytes = 400 bytes total, with no Content-Length header.
    # Reading must abort on chunk 3 (40 + 40 + 40 = 120 > 100).
    response = _StreamingResponse([b"x" * 40] * 10)
    session = MagicMock()
    session.get.return_value = response

    content, images, title = BeautifulSoupScraper(f"{_BASE}/chunked", session).scrape()

    assert (content, images, title) == ("", [], "")
    assert response.chunks_yielded == 3
    assert response.closed is True


def test_spoofed_small_content_length_still_enforces_hard_cap(monkeypatch):
    monkeypatch.setattr(bs_mod, "MAX_CONTENT_BYTES", 100)
    response = _StreamingResponse(
        [b"a" * 60, b"b" * 60, b"c" * 60],
        headers={"Content-Type": "text/html", "Content-Length": "50"},
    )
    session = MagicMock()
    session.get.return_value = response

    content, images, title = BeautifulSoupScraper(f"{_BASE}/spoofed", session).scrape()

    assert (content, images, title) == ("", [], "")
    assert response.chunks_yielded == 2
    assert response.closed is True


def test_streamed_response_within_cap_parses_and_closes(monkeypatch):
    monkeypatch.setattr(bs_mod, "MAX_CONTENT_BYTES", 1024)
    html = b"<html><head><title>Bounded Page</title></head><body><p>Hello world from stream.</p></body></html>"
    response = _StreamingResponse([html[:30], b"", html[30:]])
    session = MagicMock()
    session.get.return_value = response

    content, images, title = BeautifulSoupScraper(f"{_BASE}/ok", session).scrape()

    assert "Hello world from stream." in content
    assert title == "Bounded Page"
    assert response.closed is True


def test_exact_boundary_at_max_content_bytes_is_allowed(monkeypatch):
    html = b"<html><head><title>Exact</title></head><body><p>Boundary check</p></body></html>"
    monkeypatch.setattr(bs_mod, "MAX_CONTENT_BYTES", len(html))
    response = _StreamingResponse([html])
    session = MagicMock()
    session.get.return_value = response

    content, _, title = BeautifulSoupScraper(f"{_BASE}/exact", session).scrape()

    assert "Boundary check" in content
    assert title == "Exact"
    assert response.closed is True


def test_retry_and_error_responses_are_closed():
    first = _StreamingResponse([b"forbidden"], status_code=403)
    second = _StreamingResponse([b"not found"], status_code=404)
    session = MagicMock()
    session.get.side_effect = [first, second]

    scraper = BeautifulSoupScraper(f"{_BASE}/err", session)
    assert scraper._fetch() is None
    assert first.closed is True
    assert second.closed is True
    assert scraper.failure_reason == "HTTP_404"


def test_non_streaming_stub_still_enforces_size_cap(monkeypatch):
    monkeypatch.setattr(bs_mod, "MAX_CONTENT_BYTES", 20)

    class _StubResp:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        content = b"<html><body>this exceeds twenty bytes</body></html>"
        encoding = "utf-8"

    session = MagicMock()
    session.get.return_value = _StubResp()

    content, images, title = BeautifulSoupScraper(f"{_BASE}/stub", session).scrape()
    assert (content, images, title) == ("", [], "")
