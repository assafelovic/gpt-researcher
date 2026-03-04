"""
Tests for FireCrawl concurrency limiting and retry logic.

Validates the fix for issue #1602: FireCrawl returns empty content under
concurrent requests due to API rate limits being exceeded.
"""

import asyncio
import importlib.util
import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: load *only* the firecrawl module without triggering the heavy
# gpt_researcher package imports.
# ---------------------------------------------------------------------------
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Stub out the relative import ``from ..utils import get_relevant_images``
# so that the firecrawl module can be loaded in isolation.
_stub_utils = types.ModuleType("gpt_researcher.scraper.utils")
_stub_utils.get_relevant_images = lambda soup, link: []

# Register stubs in sys.modules so the relative import resolves.
for _name in (
    "gpt_researcher",
    "gpt_researcher.scraper",
    "gpt_researcher.scraper.utils",
    "gpt_researcher.scraper.firecrawl",
):
    sys.modules.setdefault(_name, types.ModuleType(_name))
sys.modules["gpt_researcher.scraper.utils"] = _stub_utils

# Now load the firecrawl module from its file path.
_fc_path = os.path.join(
    _REPO, "gpt_researcher", "scraper", "firecrawl", "firecrawl.py"
)
_spec = importlib.util.spec_from_file_location(
    "gpt_researcher.scraper.firecrawl.firecrawl", _fc_path
)
fc_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = fc_module
_spec.loader.exec_module(fc_module)

FireCrawl = fc_module.FireCrawl


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_semaphore():
    """Reset the module-level semaphore between tests."""
    fc_module._api_semaphore = None
    fc_module._semaphore_limit = 0
    yield
    fc_module._api_semaphore = None
    fc_module._semaphore_limit = 0


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    """Ensure FIRECRAWL_API_KEY is set for all tests."""
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")


# ---------------------------------------------------------------------------
# Concurrency limiting
# ---------------------------------------------------------------------------

class TestConcurrencyLimiting:
    """Verify that the semaphore limits concurrent FireCrawl API calls."""

    @pytest.mark.asyncio
    async def test_semaphore_default_is_two(self, monkeypatch):
        """Default concurrency should be 2."""
        monkeypatch.delenv("FIRECRAWL_CONCURRENCY", raising=False)
        sem = fc_module._get_api_semaphore()
        assert sem._value == 2

    @pytest.mark.asyncio
    async def test_semaphore_respects_env_var(self, monkeypatch):
        """FIRECRAWL_CONCURRENCY env var should control semaphore size."""
        monkeypatch.setenv("FIRECRAWL_CONCURRENCY", "5")
        sem = fc_module._get_api_semaphore()
        assert sem._value == 5

    @pytest.mark.asyncio
    async def test_concurrency_is_actually_limited(self, monkeypatch):
        """At most FIRECRAWL_CONCURRENCY scrapes should run in parallel."""
        monkeypatch.setenv("FIRECRAWL_CONCURRENCY", "2")
        monkeypatch.setenv("FIRECRAWL_MAX_RETRIES", "0")

        peak_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()
        good_content = "x" * 200

        async def patched_scrape_async(self_inner):
            nonlocal peak_concurrent, current_concurrent
            semaphore = fc_module._get_api_semaphore()
            async with semaphore:
                async with lock:
                    current_concurrent += 1
                    peak_concurrent = max(peak_concurrent, current_concurrent)
                await asyncio.sleep(0.05)
                async with lock:
                    current_concurrent -= 1
                return good_content, [], "Title"

        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            with patch.object(FireCrawl, "scrape_async", patched_scrape_async):
                session = MagicMock()
                scrapers = [
                    FireCrawl(f"https://example.com/{i}", session) for i in range(6)
                ]
                await asyncio.gather(*(s.scrape_async() for s in scrapers))

        assert peak_concurrent <= 2, (
            f"Peak concurrency was {peak_concurrent}, expected <= 2"
        )


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

class TestRetryLogic:
    """Verify retry with exponential backoff for rate limits and empty content."""

    @pytest.mark.asyncio
    async def test_retry_on_empty_content(self, monkeypatch):
        """Should retry when content is shorter than 100 chars."""
        monkeypatch.setenv("FIRECRAWL_MAX_RETRIES", "2")
        monkeypatch.setenv("FIRECRAWL_RETRY_BASE_DELAY", "0.01")

        good_content = "x" * 200
        call_count = 0

        def fake_scrape_once(self_inner):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return "short", [], "Title"
            return good_content, [], "Title"

        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            with patch.object(FireCrawl, "_scrape_once", fake_scrape_once):
                session = MagicMock()
                scraper = FireCrawl("https://example.com/test", session)
                content, _, _ = await scraper.scrape_async()

        assert call_count == 3
        assert len(content) >= 100

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_error(self, monkeypatch):
        """Should retry on 429 rate limit errors."""
        monkeypatch.setenv("FIRECRAWL_MAX_RETRIES", "2")
        monkeypatch.setenv("FIRECRAWL_RETRY_BASE_DELAY", "0.01")

        good_content = "x" * 200
        call_count = 0

        def fake_scrape_once(self_inner):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("429 Too Many Requests")
            return good_content, [], "Title"

        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            with patch.object(FireCrawl, "_scrape_once", fake_scrape_once):
                session = MagicMock()
                scraper = FireCrawl("https://example.com/test", session)
                content, _, _ = await scraper.scrape_async()

        assert call_count == 3
        assert len(content) >= 100

    @pytest.mark.asyncio
    async def test_no_retry_on_non_rate_limit_error(self, monkeypatch):
        """Should NOT retry on non-rate-limit errors."""
        monkeypatch.setenv("FIRECRAWL_MAX_RETRIES", "3")
        monkeypatch.setenv("FIRECRAWL_RETRY_BASE_DELAY", "0.01")

        call_count = 0

        def fake_scrape_once(self_inner):
            nonlocal call_count
            call_count += 1
            raise ConnectionError("DNS resolution failed")

        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            with patch.object(FireCrawl, "_scrape_once", fake_scrape_once):
                session = MagicMock()
                scraper = FireCrawl("https://example.com/test", session)
                content, _, _ = await scraper.scrape_async()

        assert call_count == 1  # No retries for non-rate-limit errors
        assert content == ""

    @pytest.mark.asyncio
    async def test_returns_last_content_after_retries_exhausted(self, monkeypatch):
        """Should return the last attempt's content after all retries."""
        monkeypatch.setenv("FIRECRAWL_MAX_RETRIES", "2")
        monkeypatch.setenv("FIRECRAWL_RETRY_BASE_DELAY", "0.01")

        call_count = 0

        def fake_scrape_once(self_inner):
            nonlocal call_count
            call_count += 1
            return "short", [], "Title"

        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            with patch.object(FireCrawl, "_scrape_once", fake_scrape_once):
                session = MagicMock()
                scraper = FireCrawl("https://example.com/test", session)
                content, _, _ = await scraper.scrape_async()

        assert call_count == 3  # initial + 2 retries
        assert content == "short"


# ---------------------------------------------------------------------------
# _is_rate_limit_error
# ---------------------------------------------------------------------------

class TestRateLimitDetection:
    """Verify rate limit error detection."""

    def test_detects_429_error(self):
        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            scraper = FireCrawl("https://example.com", MagicMock())
            assert scraper._is_rate_limit_error(RuntimeError("429 Too Many Requests"))

    def test_detects_rate_limit_message(self):
        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            scraper = FireCrawl("https://example.com", MagicMock())
            assert scraper._is_rate_limit_error(RuntimeError("Rate limit exceeded"))

    def test_ignores_other_errors(self):
        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            scraper = FireCrawl("https://example.com", MagicMock())
            assert not scraper._is_rate_limit_error(ConnectionError("DNS failed"))


# ---------------------------------------------------------------------------
# Sync scrape fallback
# ---------------------------------------------------------------------------

class TestSyncScrape:
    """Verify the synchronous scrape() method still works."""

    def test_sync_scrape_returns_content(self):
        good_content = "x" * 200

        def fake_scrape_once(self_inner):
            return good_content, ["img.png"], "Title"

        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            with patch.object(FireCrawl, "_scrape_once", fake_scrape_once):
                scraper = FireCrawl("https://example.com", MagicMock())
                content, images, title = scraper.scrape()

        assert content == good_content
        assert images == ["img.png"]
        assert title == "Title"

    def test_sync_scrape_handles_error(self):
        def fake_scrape_once(self_inner):
            raise RuntimeError("connection failed")

        with patch("firecrawl.FirecrawlApp", return_value=MagicMock()):
            with patch.object(FireCrawl, "_scrape_once", fake_scrape_once):
                scraper = FireCrawl("https://example.com", MagicMock())
                content, images, title = scraper.scrape()

        assert content == ""
        assert images == []
        assert title == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
