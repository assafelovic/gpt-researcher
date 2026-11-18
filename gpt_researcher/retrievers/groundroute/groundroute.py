"""GroundRoute search retriever for GPT Researcher.

GroundRoute routes each query across multiple web-search engines (Serper, Brave,
Exa, Tavily, Firecrawl, Perplexity), picks the cheapest that meets a quality bar,
caches repeats, and fails over — exposed as one search API.
"""

import os

import requests


class GroundRouteSearch:
    """GroundRoute multi-engine search retriever."""

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        self.query = query
        self.headers = headers or {}
        self.topic = topic
        self.base_url = "https://api.groundroute.ai/v1/search"
        self.api_key = self.get_api_key()
        self.query_domains = query_domains or None

    def get_api_key(self):
        """Get the GroundRoute API key from headers or the environment."""
        api_key = self.headers.get("groundroute_api_key")
        if not api_key:
            try:
                api_key = os.environ["GROUNDROUTE_API_KEY"]
            except KeyError:
                raise Exception(
                    "GroundRoute API key not found. Set the GROUNDROUTE_API_KEY "
                    "environment variable. Create a key at https://groundroute.ai/overview"
                )
        return api_key

    def search(self, max_results=7):
        """Search via GroundRoute. Returns [{"href": url, "body": content}, ...]."""
        if max_results <= 0:
            return []

        search_query = self.query
        if self.query_domains and len(self.query_domains) > 0:
            clean_domains = [
                d.strip()
                for d in self.query_domains
                if isinstance(d, str) and d.strip()
            ]
            if clean_domains:
                domain_query = " OR ".join(
                    [f"site:{domain}" for domain in clean_domains]
                )
                search_query = f"({domain_query}) {self.query}"

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"query": search_query, "max_results": max_results},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            print(f"Error performing GroundRoute search: {e}")
            return []

        if isinstance(payload, list):
            results = payload
        elif isinstance(payload, dict):
            results = payload.get("results", [])
        else:
            return []

        if not isinstance(results, list):
            return []

        normalized = []
        for r in results:
            if not isinstance(r, dict):
                continue
            href = r.get("url") or r.get("href") or r.get("link") or ""
            if not href:
                continue
            body = r.get("content") or r.get("snippet") or r.get("body") or ""
            item = {"href": href, "body": body}
            title = r.get("title")
            if title:
                item["title"] = title
            normalized.append(item)
            if len(normalized) >= max_results:
                break
        return normalized
