"""Microsoft Web IQ Web Search v3 retriever for GPT Researcher.

API documentation: https://webiq.microsoft.ai/documentation/overview/
"""

import logging
import os
from typing import Any
from urllib.parse import urlparse

import requests


class WebIQSearch:
    """Search the web with Microsoft Web IQ Web Search v3."""

    # Web IQ returns a URL plus a snippet whose size is set by
    # WEBIQ_MAX_LENGTH (2500 characters by default). That snippet is a preview,
    # not the article, so the page still has to be fetched -- and declaring it
    # here keeps the legacy >100-character heuristic from mistaking a long
    # snippet for already-scraped content and dropping the citation.
    requires_scraping = True

    DEFAULT_ENDPOINT = "https://api.microsoft.ai/v3/search/web"
    DEFAULT_LANGUAGE = "en"
    DEFAULT_REGION = "US"
    DEFAULT_TIMEOUT = 15
    MAX_QUERY_LENGTH = 1000

    def __init__(self, query, headers=None, query_domains=None, **kwargs: Any):
        self.logger = logging.getLogger(__name__)
        request_headers = headers or {}
        header_api_key = request_headers.get("webiq_api_key")

        self.query = str(query or "")
        if isinstance(query_domains, str):
            query_domains = [query_domains]
        self.query_domains = list(query_domains or [])
        self.endpoint = os.getenv("WEBIQ_ENDPOINT", self.DEFAULT_ENDPOINT)
        self.language = os.getenv("WEBIQ_LANGUAGE", self.DEFAULT_LANGUAGE)
        self.region = os.getenv("WEBIQ_REGION", self.DEFAULT_REGION)

        self.content_format = os.getenv("WEBIQ_CONTENT_FORMAT", "passage").strip().lower()
        if self.content_format not in {"passage", "text", "html", "markdown"}:
            self.logger.warning(
                "Unsupported WEBIQ_CONTENT_FORMAT=%r; using 'passage'",
                self.content_format,
            )
            self.content_format = "passage"

        self.max_length = self._env_int("WEBIQ_MAX_LENGTH", 2500, 1, 500000)
        self.safe_search = os.getenv("WEBIQ_SAFE_SEARCH", "strict").strip().lower()
        # Web IQ Web Search v3 documents only "off" and "strict".
        if self.safe_search not in {"off", "strict"}:
            self.logger.warning(
                "Unsupported WEBIQ_SAFE_SEARCH=%r; using 'strict'",
                self.safe_search,
            )
            self.safe_search = "strict"

        self.timeout = self._env_int("WEBIQ_TIMEOUT", self.DEFAULT_TIMEOUT, 1, 120)
        self.api_key = str(header_api_key or os.getenv("WEBIQ_API_KEY", "")).strip()
        if not self.api_key:
            raise ValueError(
                "Microsoft Web IQ API key not found. Pass webiq_api_key in "
                "headers or set the WEBIQ_API_KEY environment variable."
            )

    @staticmethod
    def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(os.getenv(name, str(default)))
        except ValueError:
            value = default
        return max(minimum, min(value, maximum))

    @staticmethod
    def _normalize_domain(value: Any) -> str:
        domain = str(value or "").strip()
        if domain.lower().startswith("site:"):
            domain = domain[5:].strip()
        if "://" in domain:
            domain = urlparse(domain).netloc
        domain = domain.split("/", 1)[0].strip()
        if (
            not domain
            or len(domain) > 253
            or any(character.isspace() for character in domain)
            or any(
                not (character.isalnum() or character in ".-:")
                for character in domain
            )
        ):
            return ""
        return domain

    def _build_query(self) -> str:
        query = self.query.strip()[: self.MAX_QUERY_LENGTH]
        domains = list(
            dict.fromkeys(
                domain
                for domain in map(self._normalize_domain, self.query_domains)
                if domain
            )
        )
        invalid_count = len(self.query_domains) - len(domains)
        if invalid_count:
            self.logger.warning(
                "Ignored %d invalid or duplicate Web IQ domain filters",
                invalid_count,
            )

        valid_count = len(domains)
        while domains:
            operators = " OR ".join(f"site:{domain}" for domain in domains)
            clause = f" site:{domains[0]}" if len(domains) == 1 else f" ({operators})"
            if len(query) + len(clause) <= self.MAX_QUERY_LENGTH:
                if len(domains) < valid_count:
                    self.logger.warning(
                        "Web IQ query limit kept %d of %d valid domain filters",
                        len(domains),
                        valid_count,
                    )
                return query + clause
            domains.pop()

        if valid_count:
            self.logger.warning(
                "Web IQ query limit left no room for %d valid domain filters",
                valid_count,
            )
        return query

    def search(self, max_results=10) -> list[dict[str, str]]:
        """Run a Web IQ search and return normalized search results."""
        try:
            result_limit = max(1, min(int(max_results), 50))
        except (TypeError, ValueError):
            result_limit = 10

        payload = {
            "query": self._build_query(),
            "maxResults": result_limit,
            "language": self.language,
            "region": self.region,
            "contentFormat": self.content_format,
            "maxLength": self.max_length,
            "safeSearch": self.safe_search,
        }
        headers = {
            "x-apikey": self.api_key,
            "content-type": "application/json",
            "accept": "application/json",
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            self.logger.warning("Microsoft Web IQ search failed: %s", exc)
            return []

        web_results = data.get("webResults") if isinstance(data, dict) else None
        if not isinstance(web_results, list):
            self.logger.warning("Microsoft Web IQ response has no webResults list")
            return []

        results = []
        for item in web_results[:result_limit]:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("clickUrl")
            if not isinstance(url, str) or not url.strip():
                continue
            title = item.get("title")
            content = item.get("content")
            results.append(
                {
                    "title": title if isinstance(title, str) else "",
                    "href": url.strip(),
                    "body": content if isinstance(content, str) else "",
                }
            )

        return results
