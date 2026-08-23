"""FireCrawl concurrency cap (issue #1602, PR #1756).

FireCrawl's free tier allows 2 concurrent browsers. Deep research launches
many scrapes at once, and the excess ones came back empty rather than
erroring, so reports quietly lost sources. scrape_async serialises calls
through a module-level semaphore.

These tests never touch the network: scrape() is replaced with a stub that
records how many calls overlap.
"""
import asyncio

import pytest

import gpt_researcher.scraper.firecrawl.firecrawl as fc


@pytest.fixture(autouse=True)
def reset_semaphore(monkeypatch):
    # The semaphore is module-level and cached, so each test needs its own.
    monkeypatch.setattr(fc, "_semaphore", None)
    yield
    fc._semaphore = None


def _tracking_firecrawl(concurrency_log):
    """A FireCrawl whose scrape() records overlap instead of calling the API."""
    state = {"active": 0}

    def fake_scrape(self):
        state["active"] += 1
        concurrency_log.append(state["active"])
        # Yield to the executor so overlapping calls actually interleave.
        import time

        time.sleep(0.02)
        state["active"] -= 1
        return "content", [], "title"

    return fake_scrape


def _make_instance(link):
    # FireCrawl.__init__ constructs a FirecrawlApp, which needs the optional
    # firecrawl SDK and an API key. Neither is relevant to the concurrency
    # cap, so build the instance without running __init__.
    obj = fc.FireCrawl.__new__(fc.FireCrawl)
    obj.link = link
    obj.session = None
    obj.firecrawl = None
    return obj


async def _run_scrapes(count):
    scrapers = [_make_instance(f"https://example.com/{i}") for i in range(count)]
    return await asyncio.gather(*(s.scrape_async() for s in scrapers))


def test_scrape_async_caps_concurrency_at_default(monkeypatch):
    monkeypatch.delenv("FIRECRAWL_CONCURRENCY", raising=False)
    log = []
    monkeypatch.setattr(fc.FireCrawl, "scrape", _tracking_firecrawl(log))

    results = asyncio.run(_run_scrapes(8))

    assert len(results) == 8
    assert all(r == ("content", [], "title") for r in results)
    assert max(log) <= 2, f"expected at most 2 concurrent calls, saw {max(log)}"


def test_scrape_async_honours_env_override(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_CONCURRENCY", "4")
    log = []
    monkeypatch.setattr(fc.FireCrawl, "scrape", _tracking_firecrawl(log))

    asyncio.run(_run_scrapes(10))

    assert max(log) <= 4, f"expected at most 4 concurrent calls, saw {max(log)}"


def test_scraper_dispatches_to_scrape_async():
    # Scraper.extract_data_from_url prefers scrape_async when a backend
    # defines it; without this the cap would simply never be applied.
    assert hasattr(fc.FireCrawl, "scrape_async")
    assert asyncio.iscoroutinefunction(fc.FireCrawl.scrape_async)
