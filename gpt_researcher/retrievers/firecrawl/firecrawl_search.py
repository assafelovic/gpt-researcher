"""Firecrawl search retriever for GPT Researcher.

Uses the Firecrawl `/v1/search` API so retrieval runs on the same paid
Firecrawl plan as scraping. Set `FIRECRAWL_API_KEY` (and optionally
`FIRECRAWL_SERVER_URL` for self-hosted instances).
"""

import json
import os

import requests


class FirecrawlSearch:
    """Firecrawl search API retriever."""

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        """
        Args:
            query (str): The search query string.
            headers (dict, optional): Optional headers with `firecrawl_api_key`.
            topic (str, optional): Unused; kept for retriever interface parity.
            query_domains (list, optional): Domains to restrict the search to.
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        self.api_key = self.headers.get("firecrawl_api_key") or os.getenv(
            "FIRECRAWL_API_KEY", ""
        )
        server_url = (
            self.headers.get("firecrawl_server_url")
            or os.getenv("FIRECRAWL_SERVER_URL")
            or "https://api.firecrawl.dev"
        )
        self.base_url = f"{server_url.rstrip('/')}/v1/search"

    def search(self, max_results=10):
        """Search the query via Firecrawl and return [{'href', 'body'}, ...]."""
        if not self.api_key:
            print(
                "Firecrawl API key not found. Set the FIRECRAWL_API_KEY environment "
                "variable to use the firecrawl retriever."
            )
            return []

        query = self.query
        if self.query_domains:
            sites = " OR ".join(f"site:{domain}" for domain in self.query_domains)
            query = f"{query} ({sites})"

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({"query": query, "limit": max_results}),
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("data", []) or []
            search_response = []
            for result in results:
                url = result.get("url")
                if not url:
                    continue
                body = (
                    result.get("markdown")
                    or result.get("description")
                    or result.get("title")
                    or ""
                )
                search_response.append({"href": url, "body": body})
            return search_response
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            return []
