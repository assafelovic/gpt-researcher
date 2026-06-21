# Keenable Retriever
# https://keenable.ai

import os
from urllib.parse import urlsplit

import requests


class KeenableSearch:
    """
    Keenable API Retriever — a web search API built for AI agents.

    Keyless by default: with no ``KEENABLE_API_KEY`` set, the free public
    endpoint is used, so this retriever works out of the box. Set
    ``KEENABLE_API_KEY`` (create one at https://keenable.ai/console) to use the
    authenticated endpoint, lift rate limits, and enable ``realtime`` mode.
    """

    def __init__(self, query, query_domains=None, **kwargs):
        """
        Initializes the KeenableSearch object.

        Args:
            query (str): The search query string.
            query_domains (list, optional): Domains to restrict the search to.
                Keenable filters by a single site, so the first domain is used.
                Defaults to None.
        """
        self.query = query
        self.query_domains = query_domains or None
        # "pro" (default, deeper retrieval) or "realtime" (low latency; requires
        # a key — not available on the keyless public endpoint).
        self.mode = os.getenv("KEENABLE_SEARCH_MODE", "pro")
        self.api_key = self.get_api_key()
        self.base_url = self.get_base_url()

    def get_api_key(self):
        """
        Gets the Keenable API key if one is configured.

        Returns:
            str: The API key, or "" to use the keyless free tier.
        """
        # A key is optional here, unlike most retrievers — Keenable defaults to
        # the keyless public endpoint, so we never raise when it is missing.
        return (os.environ.get("KEENABLE_API_KEY") or "").strip()

    def get_base_url(self):
        """
        Resolves the API base URL from ``KEENABLE_API_URL`` (HTTPS enforced).

        Returns:
            str: The base URL, defaulting to https://api.keenable.ai.
        """
        base = (os.environ.get("KEENABLE_API_URL") or "https://api.keenable.ai").rstrip("/")
        parsed = urlsplit(base)
        if parsed.hostname:
            if parsed.scheme == "https":
                return base
            # Permit plain http only against a loopback host (local dev).
            if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                return base
        raise ValueError(
            f"KEENABLE_API_URL must be an https:// URL with a host, got {base!r}"
        )

    def search(self, max_results=10):
        """
        Searches the query via the Keenable API.

        Returns:
            list: List of search results with title, href, and body.
        """
        # Keyless public endpoint by default; the keyed endpoint + X-API-Key
        # header when KEENABLE_API_KEY is set.
        if self.api_key:
            path = "/v1/search"
            headers = {"X-API-Key": self.api_key}
        else:
            path = "/v1/search/public"
            headers = {}

        headers.update({
            "Content-Type": "application/json",
            "User-Agent": "keenable-gpt-researcher",
            # Attribution header the Keenable backend segments traffic by.
            "X-Keenable-Title": "GPT-Researcher",
        })

        payload = {"query": self.query, "mode": self.mode}
        # Keenable filters by a single site; use the first domain when provided.
        if self.query_domains:
            payload["site"] = list(self.query_domains)[0]

        try:
            response = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                raise Exception("No results found with Keenable API search.")
            search_response = [
                {
                    "title": obj.get("title"),
                    "href": obj.get("url"),
                    "body": obj.get("description"),
                }
                for obj in results
                if obj.get("url")
            ]
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        # Keenable returns a fixed-size result set; honor the caller's cap.
        return search_response[:max_results]
