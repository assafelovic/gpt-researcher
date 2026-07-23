"""Regression: Scraper.extract_data_from_url must tolerate None content.

Backend scrapers occasionally return ``(None, ..., ...)`` on hard failures.
Calling ``len(content)`` before a None-check raised TypeError and could fail
an entire ``asyncio.gather`` scrape batch for one bad URL.
"""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from gpt_researcher.scraper.scraper import Scraper


class _NoneContentScraper:
    def __init__(self, link, session):
        self.link = link
        self.session = session

    def scrape(self):
        return None, None, None


class _ShortContentScraper:
    def __init__(self, link, session):
        self.link = link
        self.session = session

    def scrape(self):
        return "short", ["https://img.example/a.png"], "T"


class _OkContentScraper:
    def __init__(self, link, session):
        self.link = link
        self.session = session

    def scrape(self):
        body = "x" * 150
        return body, ["https://img.example/a.png"], "Long Enough"


@pytest.fixture
def worker_pool():
    pool = MagicMock()
    # async context manager for throttle
    cm = MagicMock()
    cm.__aenter__ = asyncio.coroutine(lambda self=None: None) if False else None

    class _Throttle:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *args):
            return False

    pool.throttle.return_value = _Throttle()
    pool.executor = None
    return pool


def _scraper_with(mock_cls, worker_pool):
    s = Scraper(
        urls=["https://example.com/page"],
        user_agent="test-agent",
        scraper="bs",
        worker_pool=worker_pool,
    )
    s.get_scraper = lambda link: mock_cls  # type: ignore[method-assign]
    s.logger = logging.getLogger("test_scraper_none_content")
    return s


@pytest.mark.asyncio
async def test_none_content_returns_empty_payload(worker_pool):
    s = _scraper_with(_NoneContentScraper, worker_pool)
    result = await s.extract_data_from_url("https://example.com/none", s.session)
    assert result["url"] == "https://example.com/none"
    assert result["raw_content"] is None
    assert result["image_urls"] == []
    assert result["title"] == ""


@pytest.mark.asyncio
async def test_short_content_returns_empty_payload(worker_pool):
    s = _scraper_with(_ShortContentScraper, worker_pool)
    result = await s.extract_data_from_url("https://example.com/short", s.session)
    assert result["raw_content"] is None
    assert result["title"] == "T"


@pytest.mark.asyncio
async def test_long_content_preserved(worker_pool):
    s = _scraper_with(_OkContentScraper, worker_pool)
    result = await s.extract_data_from_url("https://example.com/ok", s.session)
    assert result["raw_content"] == "x" * 150
    assert result["title"] == "Long Enough"
    assert result["image_urls"] == ["https://img.example/a.png"]
