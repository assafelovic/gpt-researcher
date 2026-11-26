"""NestDaddy search retriever for GPT Researcher.

NestDaddy is a search engine with its own crawler and index. Its Search & News
API returns ranked web results as JSON, with fresh news articles blended in for
current topics. Get a key at https://nestdaddy.com/serp-api
"""

import os
from urllib.parse import urlparse

import requests


class NestDaddySearch:
    """NestDaddy web search retriever."""

    MAX_RESULTS = 50

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        self.query = query
        self.headers = headers or {}
        self.topic = topic
        self.base_url = os.getenv("NESTDADDY_API_BASE", "https://nestdaddy.com").rstrip("/") + "/api/v1/search"
        self.api_key = self.get_api_key()
        self.query_domains = [
            d.strip().lower().removeprefix("www.")
            for d in (query_domains or [])
            if isinstance(d, str) and d.strip()
        ]

    def get_api_key(self):
        """Get the NestDaddy API key from headers or the environment."""
        api_key = self.headers.get("nestdaddy_api_key")
        if not api_key:
            try:
                api_key = os.environ["NESTDADDY_API_KEY"]
            except KeyError:
                raise Exception(
                    "NestDaddy API key not found. Set the NESTDADDY_API_KEY "
                    "environment variable. Get a key at https://nestdaddy.com/serp-api"
                )
        return api_key

    def _in_scope(self, url):
        """Keep a result when no domains were requested, or when it is on one of them."""
        if not self.query_domains:
            return True
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        return any(host == d or host.endswith("." + d) for d in self.query_domains)

    def search(self, max_results=7):
        """Search via NestDaddy. Returns [{"title": ..., "href": url, "body": snippet}, ...]."""
        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            return []
        if max_results <= 0:
            return []

        # Ask for extra rows when filtering by domain, so the filter still has enough to keep.
        limit = min(self.MAX_RESULTS, max_results * 3 if self.query_domains else max_results)
        try:
            response = requests.get(
                self.base_url,
                headers={"X-API-Key": self.api_key},
                params={"q": self.query, "limit": limit},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            print(f"Error performing NestDaddy search: {e}")
            return []

        if not isinstance(payload, dict) or payload.get("success") is False:
            return []
        results = payload.get("results")
        if not isinstance(results, list):
            return []

        normalized = []
        for r in results:
            if not isinstance(r, dict):
                continue
            href = r.get("url")
            if not isinstance(href, str) or not href.startswith(("http://", "https://")):
                continue
            if not self._in_scope(href):
                continue
            body = r.get("snippet") or r.get("description") or ""
            normalized.append({"title": r.get("title") or "", "href": href, "body": body})
            if len(normalized) >= max_results:
                break
        return normalized
