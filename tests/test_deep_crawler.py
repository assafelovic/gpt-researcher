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


def test_canonicalize_url_rejects_repeated_path_segments():
    url = "https://example.com/local-news/swiss-news-homepage/swiss-news-homepage/swiss-news-homepage/"

    assert deep_crawler._canonicalize_url(url) is None


def test_canonicalize_url_rejects_path_loops_with_malformed_segment():
    url = "https://example.com/local-news/扶余-swiss-news-homepage/swiss-news-homepage/swiss-news-homepage/"

    assert deep_crawler._canonicalize_url(url) is None


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

    async def fake_fetch_page_html(url, user_agent, timeout, proxy_url=None):
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
async def test_prioritize_and_expand_urls_skips_repeated_path_loops(monkeypatch):
    html = """
    <html>
      <head><title>Swiss News</title></head>
      <body>
        <a href="swiss-news-homepage">Homepage</a>
      </body>
    </html>
    """

    async def fake_fetch_page_html(url, user_agent, timeout, proxy_url=None):
        return html, url, "text/html"

    monkeypatch.setattr(deep_crawler, "_fetch_page_html", fake_fetch_page_html)

    results = await deep_crawler.prioritize_and_expand_urls(
        query="Swiss news homepage",
        candidate_entries=[
            {
                "url": "https://example.com/local-news/swiss-news-homepage/",
                "title": "Swiss News",
                "snippet": "Homepage",
                "source": "duckduckgo",
            }
        ],
        cfg=_crawler_cfg(),
        query_domains=[],
        visited_urls=set(),
    )

    urls = [entry["url"] for entry in results]

    assert any("local-news/swiss-news-homepage" in url for url in urls)
    assert all("swiss-news-homepage/swiss-news-homepage" not in url for url in urls)


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
            self.report_source = "web"

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


class TestPathSegmentSignature:
    def test_normal_segments(self):
        assert deep_crawler._path_segment_signature("HelloWorld") == "helloworld"
        assert deep_crawler._path_segment_signature("foo-bar") == "foo-bar"
        assert deep_crawler._path_segment_signature("ABC") == "abc"

    def test_mixed_case(self):
        assert deep_crawler._path_segment_signature("FOO") == "foo"
        assert deep_crawler._path_segment_signature("FooBar") == "foobar"
        assert deep_crawler._path_segment_signature("UPPER-lower") == "upper-lower"

    def test_non_ascii(self):
        result = deep_crawler._path_segment_signature("Über")
        assert result == "ber"
        result = deep_crawler._path_segment_signature("日本語")
        assert result == "日本語"
        result = deep_crawler._path_segment_signature("café")
        assert result == "caf"

    def test_empty_segments(self):
        assert deep_crawler._path_segment_signature("") == ""
        assert deep_crawler._path_segment_signature("   ") == ""

    def test_special_characters(self):
        assert deep_crawler._path_segment_signature("!!hello!!") == "hello"
        assert deep_crawler._path_segment_signature("a---b") == "a-b"
        assert deep_crawler._path_segment_signature("-x-") == "x"
        assert deep_crawler._path_segment_signature("foo_bar") == "foo-bar"


class TestHasRepeatedPathSegmentChain:
    def test_zero_or_one_segments(self):
        assert deep_crawler._has_repeated_path_segment_chain([]) is False
        assert deep_crawler._has_repeated_path_segment_chain(["a"]) is False

    def test_repeating_alternating_chain(self):
        assert deep_crawler._has_repeated_path_segment_chain(["a", "b", "a", "b"]) is False
        assert deep_crawler._has_repeated_path_segment_chain(["x", "y", "x", "y", "x"]) is False

    def test_no_repeat(self):
        assert deep_crawler._has_repeated_path_segment_chain(["a", "b", "c"]) is False

    def test_direct_repeat(self):
        assert deep_crawler._has_repeated_path_segment_chain(["a", "a"]) is True
        assert deep_crawler._has_repeated_path_segment_chain(["a", "a", "b"]) is True

    def test_mixed_case_repeats(self):
        assert deep_crawler._has_repeated_path_segment_chain(["Foo", "foo"]) is True
        assert deep_crawler._has_repeated_path_segment_chain(["FOO", "foo", "FOO"]) is True

    def test_unicode_repeats(self):
        assert deep_crawler._has_repeated_path_segment_chain(["über", "ÜBER"]) is True
        assert deep_crawler._has_repeated_path_segment_chain(["straße", "STRASSE"]) is True


class TestCollapseRepeatedPathSegments:
    def test_basic_collapse(self):
        assert deep_crawler._collapse_repeated_path_segments(["a", "a", "b"]) == ["a", "b"]

    def test_case_insensitive_collapse(self):
        result = deep_crawler._collapse_repeated_path_segments(["foo", "FOO", "bar"])
        assert len(result) == 2
        assert deep_crawler._path_segment_signature(result[0]) == "foo"
        assert result[1] == "bar"

    def test_empty_input(self):
        assert deep_crawler._collapse_repeated_path_segments([]) == []

    def test_single_segment(self):
        assert deep_crawler._collapse_repeated_path_segments(["a"]) == ["a"]

    def test_triple_repeat(self):
        assert deep_crawler._collapse_repeated_path_segments(["x", "x", "x", "y"]) == ["x", "y"]

    def test_no_repeat(self):
        assert deep_crawler._collapse_repeated_path_segments(["a", "b", "c"]) == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_fetch_page_html_network_error_returns_none():
    html, url, content_type = await deep_crawler._fetch_page_html(
        "http://localhost:1/nonexistent",
        "pytest-agent",
        0.1,
    )
    assert html is None
    assert url is None
    assert content_type is None


@pytest.mark.asyncio
async def test_fetch_page_html_timeout_returns_none():
    html, url, content_type = await deep_crawler._fetch_page_html(
        "https://127.0.0.1:1/timeout",
        "pytest-agent",
        0.001,
    )
    assert html is None
    assert url is None
    assert content_type is None


class TestAllowedCandidate:
    def test_rejects_unsupported_scheme(self):
        assert deep_crawler._allowed_candidate(
            "ftp://example.com/file", query_domains=None, root_host=None, allow_external_links=True
        ) is False

    def test_rejects_javascript_mailto_tel(self):
        assert deep_crawler._allowed_candidate(
            "javascript:void(0)", query_domains=None, root_host=None, allow_external_links=True
        ) is False
        assert deep_crawler._allowed_candidate(
            "mailto:user@example.com", query_domains=None, root_host=None, allow_external_links=True
        ) is False
        assert deep_crawler._allowed_candidate(
            "tel:+1234567890", query_domains=None, root_host=None, allow_external_links=True
        ) is False

    def test_rejects_noise_links(self):
        assert deep_crawler._allowed_candidate(
            "https://example.com/login", query_domains=None, root_host="example.com", allow_external_links=False
        ) is False
        assert deep_crawler._allowed_candidate(
            "https://example.com/privacy", query_domains=None, root_host="example.com", allow_external_links=False
        ) is False

    def test_allows_external_when_permitted(self):
        assert deep_crawler._allowed_candidate(
            "https://other.com/page", query_domains=None, root_host="example.com", allow_external_links=True
        ) is True

    def test_rejects_external_when_not_permitted(self):
        assert deep_crawler._allowed_candidate(
            "https://other.com/page", query_domains=None, root_host="example.com", allow_external_links=False
        ) is False

    def test_uses_query_domains_when_provided(self):
        assert deep_crawler._allowed_candidate(
            "https://docs.python.org/guide",
            query_domains=["python.org"],
            root_host=None,
            allow_external_links=False,
        ) is True
        assert deep_crawler._allowed_candidate(
            "https://other.com/page",
            query_domains=["python.org"],
            root_host=None,
            allow_external_links=False,
        ) is False


class TestCanonicalizeUrl:
    def test_removes_trailing_slash(self):
        assert deep_crawler._canonicalize_url("http://example.com/foo/") == "http://example.com/foo"

    def test_preserves_url_without_trailing_slash(self):
        assert deep_crawler._canonicalize_url("http://example.com/foo") == "http://example.com/foo"

    def test_handles_parent_dir_reference(self):
        url = deep_crawler._canonicalize_url("http://example.com/a/b/../c")
        assert url is not None
        assert url.startswith("http://example.com")

    def test_root_url_normalization(self):
        assert deep_crawler._canonicalize_url("http://example.com/") == "http://example.com"
        assert deep_crawler._canonicalize_url("http://example.com") == "http://example.com"

    def test_empty_or_none(self):
        assert deep_crawler._canonicalize_url("") is None
        assert deep_crawler._canonicalize_url(None) is None

    def test_tracking_params_removed(self):
        url = deep_crawler._canonicalize_url("http://example.com/page?utm_source=twitter&q=hello")
        assert url is not None
        assert "utm_source" not in url
        assert "q=hello" in url
