from types import SimpleNamespace

import pytest

from gpt_researcher.actions import deep_crawler
from gpt_researcher.skills.researcher import ResearchConductor


def _crawler_cfg(**overrides):
    base = {
        "enable_deep_crawler": True,
        "deep_crawler_depth": 1,
        "deep_crawler_breadth": 3,
        "deep_crawler_concurrency": 2,
        "deep_crawler_max_pages": 6,
        "deep_crawler_max_links_per_page": 10,
        "deep_crawler_allow_external_links": False,
        "deep_crawler_timeout": 1.0,
        "user_agent": "pytest-agent",
        "max_search_results_per_query": 5,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_score_url_candidate_prefers_docs_pages_over_login_pages():
    query = "FastAPI async API docs"

    docs_score = deep_crawler.score_url_candidate(
        query=query,
        url="https://fastapi.tiangolo.com/tutorial/response-model/",
        title="FastAPI Tutorial",
        snippet="Official docs for FastAPI",
        root_host="fastapi.tiangolo.com",
    )
    login_score = deep_crawler.score_url_candidate(
        query=query,
        url="https://fastapi.tiangolo.com/login",
        title="Login",
        snippet="Sign in to your account",
        root_host="fastapi.tiangolo.com",
    )

    assert docs_score > login_score


@pytest.mark.asyncio
async def test_prioritize_and_expand_urls_discovers_same_domain_links(monkeypatch):
    html = """
    <html>
      <head><title>FastAPI Docs</title></head>
      <body>
        <a href="/tutorial/">Tutorial</a>
        <a href="/reference/">Reference</a>
        <a href="https://fastapi.tiangolo.com/login">Login</a>
        <a href="https://other.example.com/guide">External Guide</a>
      </body>
    </html>
    """

    async def fake_fetch_page_html(url, user_agent, timeout):
        return html, url, "text/html"

    monkeypatch.setattr(deep_crawler, "_fetch_page_html", fake_fetch_page_html)

    results = await deep_crawler.prioritize_and_expand_urls(
        query="FastAPI async API docs",
        candidate_entries=[
            {
                "url": "https://fastapi.tiangolo.com/",
                "title": "FastAPI",
                "snippet": "Official docs",
                "source": "duckduckgo",
            }
        ],
        cfg=_crawler_cfg(),
        query_domains=[],
        visited_urls=set(),
    )

    urls = [entry["url"] for entry in results]

    assert any("fastapi.tiangolo.com/tutorial" in url for url in urls)
    assert any("fastapi.tiangolo.com/reference" in url for url in urls)
    assert all("login" not in url for url in urls)
    assert all("other.example.com" not in url for url in urls)


@pytest.mark.asyncio
async def test_research_conductor_uses_crawler_order(monkeypatch):
    class FakeRetriever:
        pass

    class FakeResearcher:
        def __init__(self):
            self.retrievers = [FakeRetriever]
            self.cfg = _crawler_cfg()
            self.visited_urls = set()
            self.verbose = False
            self.websocket = None
            self.query_domains = []

        def add_research_sources(self, sources):
            return None

    async def fake_get_search_results(query, retriever, query_domains=None, researcher=None):
        return [
            {"href": "https://example.com/a", "title": "A", "body": "Body A"},
            {"href": "https://example.com/b", "title": "B", "body": "Body B"},
        ]

    async def fake_prioritize_and_expand_urls(**kwargs):
        return [
            {"url": "https://example.com/b"},
            {"url": "https://example.com/a"},
            {"url": "https://example.com/c"},
        ]

    monkeypatch.setattr("gpt_researcher.skills.researcher.get_search_results", fake_get_search_results)
    monkeypatch.setattr("gpt_researcher.skills.researcher.prioritize_and_expand_urls", fake_prioritize_and_expand_urls)

    conductor = ResearchConductor(FakeResearcher())
    urls, prefetched_content = await conductor._search_relevant_source_urls("FastAPI vs Flask")

    assert urls == [
        "https://example.com/b",
        "https://example.com/a",
        "https://example.com/c",
    ]
    assert prefetched_content == []
