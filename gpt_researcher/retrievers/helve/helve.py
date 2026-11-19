"""Helve search retriever for GPT Researcher."""

import os

import requests


class HelveSearch:
    """Helve web search retriever."""

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        self.query = query
        self.headers = headers or {}
        self.topic = topic
        self.base_url = "https://helve.dev/v1/search"
        self.api_key = self.get_api_key()
        self.provider = (
            self.headers.get("helve_provider")
            or os.environ.get("HELVE_SEARCH_PROVIDER")
            or "auto"
        )
        self.query_domains = query_domains or None

    def get_api_key(self):
        """Get the Helve API key from headers or the environment."""
        api_key = self.headers.get("helve_api_key")
        if not api_key:
            try:
                api_key = os.environ["HELVE_API_KEY"]
            except KeyError:
                raise Exception(
                    "Helve API key not found. Set the HELVE_API_KEY "
                    "environment variable. Create a key at "
                    "https://helve.dev"
                )
        return api_key

    def search(self, max_results=7):
        """Search via Helve. Returns [{"href": url, "body": content}, ...]."""
        body = {
            "query": self.query,
            "provider": self.provider,
            "max_results": max_results,
        }
        if self.query_domains:
            body["include_domains"] = list(self.query_domains)

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            print(f"Error performing Helve search: {e}")
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
            snippets = r.get("snippets")
            if isinstance(snippets, list):
                snippet_text = "\n".join(s for s in snippets if isinstance(s, str) and s)
            else:
                snippet_text = ""
            content = (
                r.get("full_text")
                or snippet_text
                or r.get("summary")
                or r.get("content")
                or r.get("snippet")
                or r.get("body")
                or ""
            )
            normalized.append({"href": href, "body": content})
            if len(normalized) >= max_results:
                break
        return normalized
