"""Bounded deep-crawl helpers for GPT Researcher.

The crawler is intentionally conservative: it ranks seed URLs, follows a small
number of same-domain/documentation-style links, and returns prioritized URL
entries for the existing scraper pipeline. The goal is to improve source
coverage and source quality without turning research into an uncontrolled crawl.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse, urldefrag

import requests
from bs4 import BeautifulSoup

from gpt_researcher.scraper.browser.processing.html import extract_hyperlinks
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.utils.network import build_requests_proxies

from .query_processing import _extract_focus_terms

logger = get_formatted_logger()

_DOC_HINTS = (
    "docs",
    "documentation",
    "reference",
    "api",
    "guide",
    "manual",
    "tutorial",
    "learn",
    "developer",
    "sdk",
    "examples",
    "getting-started",
    "quickstart",
    "help",
    "wiki",
)

_NOISE_HINTS = (
    "login",
    "logout",
    "sign-in",
    "signin",
    "signup",
    "register",
    "account",
    "privacy",
    "terms",
    "cookie",
    "careers",
    "jobs",
    "contact",
    "cart",
    "checkout",
    "share",
    "rss",
    "feed",
    "sitemap",
    "author",
    "tag",
    "category",
)

_TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid", "ref")
_SUPPORTED_SCHEMES = {"http", "https"}


def _normalize_host(host: str | None) -> str:
    if not host:
        return ""
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def _extract_host(url: str | None) -> str:
    if not url:
        return ""
    return _normalize_host(urlparse(url).netloc)


def _normalize_domain_entry(domain: str | None) -> str:
    if not domain:
        return ""
    parsed = urlparse(domain)
    if parsed.netloc:
        return _normalize_host(parsed.netloc)
    return _normalize_host(parsed.path or domain)


def _host_matches(host: str, domain: str) -> bool:
    host = _normalize_host(host)
    domain = _normalize_host(domain)
    if not host or not domain:
        return False
    return host == domain or host.endswith(f".{domain}")


def _canonicalize_url(url: str | None) -> str | None:
    if not url:
        return None

    parsed = urlparse(url.strip())
    if parsed.scheme and parsed.scheme.lower() not in _SUPPORTED_SCHEMES:
        return None

    if not parsed.scheme:
        return None

    query_parts = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith(_TRACKING_QUERY_PREFIXES)
    ]
    cleaned = parsed._replace(
        netloc=_normalize_host(parsed.netloc),
        query=urlencode(query_parts, doseq=True),
    )
    cleaned_url = urlunparse(cleaned)
    cleaned_url, _fragment = urldefrag(cleaned_url)
    return cleaned_url.rstrip("/") if cleaned_url.endswith("/") and cleaned_url not in {"http://", "https://"} else cleaned_url


def _candidate_text(*parts: str | None) -> str:
    return " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip()).lower()


def _has_hint(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)


def _term_overlap(query_terms: list[str], candidate_text: str) -> tuple[int, int]:
    if not query_terms:
        return 0, 0
    hits = [term for term in query_terms if term and term in candidate_text]
    return len(hits), len(query_terms)


def score_url_candidate(
    query: str,
    url: str,
    title: str = "",
    snippet: str = "",
    anchor_text: str = "",
    query_domains: list[str] | None = None,
    root_host: str | None = None,
    depth: int = 0,
    from_search: bool = True,
) -> float:
    """Assign a bounded relevance score to a URL candidate."""
    canonical_url = _canonicalize_url(url)
    if not canonical_url:
        return float("-inf")

    parsed = urlparse(canonical_url)
    host = _normalize_host(parsed.netloc)
    text = _candidate_text(canonical_url, title, snippet, anchor_text, parsed.path, parsed.query)
    query_terms = _extract_focus_terms(query)
    if not query_terms:
        query_terms = [term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2]

    score = 0.0

    if query_domains:
        normalized_domains = [_normalize_domain_entry(domain) for domain in query_domains]
        if any(_host_matches(host, domain) for domain in normalized_domains if domain):
            score += 40.0
        else:
            score -= 15.0
    elif root_host:
        if _host_matches(host, root_host):
            score += 24.0
        elif host and _normalize_host(root_host) in host:
            score += 8.0

    overlap_hits, overlap_total = _term_overlap(query_terms, text)
    if overlap_total:
        score += min(26.0, overlap_hits * 6.0)

    if _has_hint(text, _DOC_HINTS):
        score += 12.0
    if _has_hint(text, _NOISE_HINTS):
        score -= 35.0

    if canonical_url.endswith(".pdf"):
        score += 7.0

    if parsed.scheme == "https":
        score += 1.5

    if title:
        score += 2.5
    if snippet:
        score += 1.5
    if anchor_text:
        score += 3.0

    if from_search:
        score += 4.0

    if depth:
        score -= min(12.0, depth * 3.0)

    if len(canonical_url) > 180:
        score -= 4.0

    if "?" in canonical_url and "api" not in text and "docs" not in text:
        score -= 1.0

    return score


def _entry_root_host(entry: dict[str, Any], query_domains: list[str] | None) -> str:
    if query_domains:
        return ""
    root_host = entry.get("root_host")
    if isinstance(root_host, str) and root_host.strip():
        return _normalize_host(root_host)
    return _extract_host(entry.get("url"))


def _normalize_candidate_entry(
    query: str,
    entry: dict[str, Any],
    query_domains: list[str] | None,
    visited_urls: set[str],
    depth: int = 0,
    parent_url: str | None = None,
    from_search: bool = True,
) -> dict[str, Any] | None:
    url = _canonicalize_url(entry.get("url"))
    if not url:
        return None

    if url in visited_urls:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in _SUPPORTED_SCHEMES:
        return None

    host = _normalize_host(parsed.netloc)
    root_host = _entry_root_host(entry, query_domains)
    if query_domains:
        normalized_domains = [_normalize_domain_entry(domain) for domain in query_domains]
        if not any(_host_matches(host, domain) for domain in normalized_domains if domain):
            return None
    elif root_host and not _host_matches(host, root_host):
        return None

    title = str(entry.get("title", "") or "").strip()
    snippet = str(
        entry.get("snippet")
        or entry.get("body")
        or entry.get("content")
        or entry.get("raw_content")
        or ""
    ).strip()
    anchor_text = str(entry.get("anchor_text", "") or "").strip()
    source = str(entry.get("source", "") or "").strip()

    score = score_url_candidate(
        query=query,
        url=url,
        title=title,
        snippet=snippet,
        anchor_text=anchor_text,
        query_domains=query_domains,
        root_host=root_host,
        depth=depth,
        from_search=from_search,
    )

    return {
        "url": url,
        "title": title,
        "snippet": snippet,
        "anchor_text": anchor_text,
        "source": source,
        "parent_url": parent_url,
        "depth": depth,
        "score": score,
        "host": host,
        "root_host": root_host,
        "from_search": from_search,
    }


def _dedupe_ranked_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in sorted(
        entries,
        key=lambda item: (
            -float(item.get("score", 0.0)),
            int(item.get("depth", 0)),
            str(item.get("url", "")),
        ),
    ):
        url = entry.get("url")
        if not isinstance(url, str) or not url or url in seen:
            continue
        seen.add(url)
        ranked.append(entry)
    return ranked


def _allowed_candidate(url: str, query_domains: list[str] | None, root_host: str | None, allow_external_links: bool) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in _SUPPORTED_SCHEMES:
        return False

    candidate_text = _candidate_text(url, parsed.path, parsed.query)
    if _has_hint(candidate_text, ("javascript:", "mailto:", "tel:")):
        return False

    if _has_hint(candidate_text, ("logout", "signout", "signin", "login", "register", "privacy", "terms", "cookie")):
        return False

    host = _normalize_host(parsed.netloc)
    if query_domains:
        normalized_domains = [_normalize_domain_entry(domain) for domain in query_domains]
        return any(_host_matches(host, domain) for domain in normalized_domains if domain)

    if allow_external_links:
        return True

    return _host_matches(host, root_host or host)


async def _fetch_page_html(
    url: str,
    user_agent: str,
    timeout: float,
    proxy_url: str | None = None,
) -> tuple[str | None, str | None, str | None]:
    def _fetch() -> tuple[str | None, str | None, str | None]:
        response = requests.get(
            url,
            headers={"User-Agent": user_agent},
            proxies=build_requests_proxies(proxy_url),
            timeout=timeout,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        return response.text, response.url, content_type

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as exc:
        logger.debug("Failed to fetch crawl page %s: %s", url, exc, exc_info=True)
        return None, None, None


def _extract_page_candidates(
    query: str,
    source_entry: dict[str, Any],
    html: str,
    final_url: str,
    query_domains: list[str] | None,
    visited_urls: set[str],
    max_links_per_page: int,
    allow_external_links: bool,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = ""
    if soup.title and soup.title.string:
        page_title = soup.title.string.strip()

    hyperlinks = extract_hyperlinks(soup, final_url)[:max_links_per_page]
    children: list[dict[str, Any]] = []
    parent_root_host = source_entry.get("root_host") or _extract_host(final_url)
    parent_depth = int(source_entry.get("depth", 0))

    for anchor_text, link_url in hyperlinks:
        candidate_url = _canonicalize_url(link_url)
        if not candidate_url or candidate_url in visited_urls:
            continue

        if not _allowed_candidate(candidate_url, query_domains, parent_root_host, allow_external_links):
            continue

        child_entry = {
            "url": candidate_url,
            "title": page_title,
            "snippet": source_entry.get("snippet", ""),
            "anchor_text": anchor_text,
            "source": source_entry.get("source", ""),
            "parent_url": source_entry.get("url"),
            "depth": parent_depth + 1,
            "root_host": parent_root_host,
            "from_search": False,
        }
        normalized = _normalize_candidate_entry(
            query=query,
            entry=child_entry,
            query_domains=query_domains,
            visited_urls=visited_urls,
            depth=parent_depth + 1,
            parent_url=source_entry.get("url"),
            from_search=False,
        )
        if normalized:
            children.append(normalized)

    return _dedupe_ranked_entries(children)


async def prioritize_and_expand_urls(
    query: str,
    candidate_entries: list[dict[str, Any]],
    cfg: Any,
    query_domains: list[str] | None = None,
    visited_urls: set[str] | list[str] | None = None,
    proxy_url: str | None = None,
) -> list[dict[str, Any]]:
    """Rank seed URLs and optionally expand them through a bounded crawl."""
    query_domains = query_domains or []
    visited_set = {
        _canonicalize_url(url) or str(url)
        for url in (visited_urls or [])
        if url
    }

    enable_deep_crawler = getattr(cfg, "enable_deep_crawler", True)
    max_depth = max(0, int(getattr(cfg, "deep_crawler_depth", 1) or 0))
    breadth_limit = max(1, int(getattr(cfg, "deep_crawler_breadth", 4) or 1))
    concurrency_limit = max(1, int(getattr(cfg, "deep_crawler_concurrency", 3) or 1))
    max_pages = max(1, int(getattr(cfg, "deep_crawler_max_pages", 12) or 12))
    max_links_per_page = max(1, int(getattr(cfg, "deep_crawler_max_links_per_page", 24) or 24))
    allow_external_links = bool(getattr(cfg, "deep_crawler_allow_external_links", False))
    request_timeout = float(getattr(cfg, "deep_crawler_timeout", 8.0) or 8.0)
    user_agent = getattr(
        cfg,
        "user_agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    )

    ranked_seed_entries: list[dict[str, Any]] = []
    for entry in candidate_entries:
        normalized = _normalize_candidate_entry(
            query=query,
            entry=entry,
            query_domains=query_domains,
            visited_urls=visited_set,
            depth=0,
            parent_url=None,
            from_search=True,
        )
        if normalized:
            ranked_seed_entries.append(normalized)

    ranked_seed_entries = _dedupe_ranked_entries(ranked_seed_entries)
    if not ranked_seed_entries:
        return []

    if not enable_deep_crawler or max_depth <= 0:
        return ranked_seed_entries[:max_pages]

    seed_frontier = ranked_seed_entries[:breadth_limit]
    discovered_entries = list(ranked_seed_entries)
    frontier = seed_frontier
    seen_urls = set(visited_set)
    seen_urls.update(entry["url"] for entry in ranked_seed_entries)

    semaphore = asyncio.Semaphore(concurrency_limit)

    async def crawl_one(entry: dict[str, Any]) -> list[dict[str, Any]]:
        async with semaphore:
            html, final_url, content_type = await _fetch_page_html(
                entry["url"],
                user_agent,
                request_timeout,
                proxy_url=proxy_url,
            )
            if not html or not final_url:
                return []

            if content_type and "html" not in content_type.lower() and "xml" not in content_type.lower():
                return []

            if len(html) < 256:
                return []

            return _extract_page_candidates(
                query=query,
                source_entry=entry,
                html=html,
                final_url=final_url,
                query_domains=query_domains,
                visited_urls=seen_urls,
                max_links_per_page=max_links_per_page,
                allow_external_links=allow_external_links,
            )

    for _depth in range(1, max_depth + 1):
        if not frontier or len(discovered_entries) >= max_pages:
            break

        batch = frontier[:breadth_limit]
        crawled_batches = await asyncio.gather(*(crawl_one(entry) for entry in batch))

        next_frontier: list[dict[str, Any]] = []
        for crawled in crawled_batches:
            for entry in crawled:
                url = entry.get("url")
                if not isinstance(url, str) or not url:
                    continue
                if url in seen_urls:
                    continue
                if not _allowed_candidate(
                    url,
                    query_domains=query_domains,
                    root_host=entry.get("root_host"),
                    allow_external_links=allow_external_links,
                ):
                    continue

                seen_urls.add(url)
                discovered_entries.append(entry)

                if entry.get("depth", 0) < max_depth:
                    next_frontier.append(entry)

                if len(discovered_entries) >= max_pages:
                    break
            if len(discovered_entries) >= max_pages:
                break

        frontier = _dedupe_ranked_entries(next_frontier)[:breadth_limit]

    return _dedupe_ranked_entries(discovered_entries)[:max_pages]
