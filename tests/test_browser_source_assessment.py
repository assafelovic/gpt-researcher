from types import SimpleNamespace

import pytest

from gpt_researcher.skills import browser as browser_module
from gpt_researcher.skills.browser import BrowserManager


class FakeResearcher:
    def __init__(self, *, source_assessment_prompt=None):
        self.cfg = SimpleNamespace(max_scraper_workers=1, scraper_rate_limit_delay=0)
        self.verbose = False
        self.websocket = None
        self.source_assessment_prompt = source_assessment_prompt
        self.research_sources = []
        self.research_images = []
        self.rejected_sources = []
        self.source_assessor = None

    def add_research_sources(self, sources):
        self.research_sources.extend(sources)

    def add_research_images(self, images):
        self.research_images.extend(images)

    def get_research_images(self):
        return self.research_images

    def add_rejected_sources(self, sources):
        self.rejected_sources.extend(sources)


@pytest.mark.asyncio
async def test_browse_urls_returns_and_stores_only_accepted_sources(monkeypatch):
    accepted_source = {
        "url": "https://example.com/accepted",
        "title": "Accepted",
        "raw_content": "accepted",
        "image_urls": [{"url": "https://img.example/accepted.jpg", "score": 1}],
    }
    rejected_source = {
        "url": "https://example.com/rejected",
        "title": "Rejected",
        "raw_content": "rejected",
        "image_urls": [{"url": "https://img.example/rejected.jpg", "score": 100}],
    }

    async def fake_scrape_urls(urls, cfg, worker_pool):
        return [accepted_source, rejected_source], [
            {"url": "https://img.example/accepted.jpg", "score": 1},
            {"url": "https://img.example/rejected.jpg", "score": 100},
        ]

    class FakeSourceAssessor:
        async def assess_sources(self, sources):
            assert sources == [accepted_source, rejected_source]
            return [accepted_source], [
                {
                    "url": "https://example.com/rejected",
                    "title": "Rejected",
                    "accepted": False,
                    "score": 0.0,
                    "reason": "Rejected by policy.",
                    "matched_policy": "policy",
                }
            ]

    monkeypatch.setattr(browser_module, "scrape_urls", fake_scrape_urls)
    researcher = FakeResearcher(source_assessment_prompt="policy")
    researcher.source_assessor = FakeSourceAssessor()

    result = await BrowserManager(researcher).browse_urls(["https://example.com/a"])

    assert result == [accepted_source]
    assert researcher.research_sources == [accepted_source]
    assert researcher.rejected_sources[0]["url"] == "https://example.com/rejected"
    assert researcher.research_images == ["https://img.example/accepted.jpg"]


@pytest.mark.asyncio
async def test_browse_urls_default_behavior_is_unchanged(monkeypatch):
    sources = [
        {
            "url": "https://example.com/one",
            "title": "One",
            "raw_content": "one",
            "image_urls": [{"url": "https://img.example/one.jpg", "score": 1}],
        },
        {
            "url": "https://example.com/two",
            "title": "Two",
            "raw_content": "two",
            "image_urls": [{"url": "https://img.example/two.jpg", "score": 10}],
        },
    ]
    images = [
        {"url": "https://img.example/one.jpg", "score": 1},
        {"url": "https://img.example/two.jpg", "score": 10},
    ]

    async def fake_scrape_urls(urls, cfg, worker_pool):
        return sources, images

    monkeypatch.setattr(browser_module, "scrape_urls", fake_scrape_urls)
    researcher = FakeResearcher()

    result = await BrowserManager(researcher).browse_urls(["https://example.com/a"])

    assert result == sources
    assert researcher.research_sources == sources
    assert researcher.rejected_sources == []
    assert researcher.research_images == [
        "https://img.example/two.jpg",
        "https://img.example/one.jpg",
    ]
