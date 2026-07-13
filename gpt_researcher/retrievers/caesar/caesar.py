"""Caesar API search retriever for GPT Researcher.

This module provides the CaesarSearch class for performing web searches
using Caesar, an agentic web-search API. Caesar requires an API key, read
from the CAESAR_API_KEY environment variable.

Docs: https://docs.trycaesar.com
"""

import json
import os

import requests


class CaesarSearch:
    """
    Caesar API Retriever
    """

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        """
        Initializes the CaesarSearch object.

        Args:
            query (str): The search query string.
            headers (dict, optional): Additional headers to include in the request. Defaults to None.
            topic (str, optional): The topic for the search. Defaults to "general".
            query_domains (list, optional): List of domains to include in the search. Defaults to None.
        """
        input_headers = headers or {}
        self.query = query
        self.topic = topic
        self.base_url = self.get_base_url(input_headers)
        self.api_key = self.get_api_key(input_headers)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.query_domains = query_domains or None

    def get_api_key(self, headers):
        """
        Gets the Caesar API key.

        Caesar requires an API key on every request.
        Args:
            headers (dict): The headers passed to the retriever.
        Returns:
            The API key string.
        """
        api_key = headers.get("caesar_api_key")
        if not api_key:
            try:
                api_key = os.environ["CAESAR_API_KEY"]
            except KeyError:
                raise Exception(
                    "Caesar API key not found. Please set the CAESAR_API_KEY environment variable. "
                    "You can obtain your key from https://app.trycaesar.com"
                )
        return api_key

    def get_base_url(self, headers):
        """
        Gets the Caesar base URL, allowing overrides.

        Defaults to the public API at https://alpha.api.trycaesar.com. Override
        with the CAESAR_API_URL environment variable (or the caesar_api_url
        header).
        Args:
            headers (dict): The headers passed to the retriever.
        Returns:
            The base URL (without a trailing slash).
        """
        base_url = headers.get("caesar_api_url") or os.environ.get(
            "CAESAR_API_URL", "https://alpha.api.trycaesar.com"
        )
        return base_url.rstrip("/")

    def _search(self, query: str, max_results: int = 10) -> dict:
        """
        Internal search method to send the request to the API.
        """

        data = {
            "query": query,
            "max_results": max_results,
        }
        if self.query_domains:
            data["source_policy"] = {"include_domains": self.query_domains}

        response = requests.post(
            f"{self.base_url}/v1/search",
            data=json.dumps(data),
            headers=self.headers,
            timeout=100,
        )
        # Raises a HTTPError if the HTTP request returned an unsuccessful status code
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _body(obj: dict) -> str:
        """
        Builds the result body.

        Caesar's `snippet` is the page's meta description, so it is identical for
        every query that surfaces the document. Its `passages` are the spans Caesar
        selected for this query, so they carry the text that actually answers it.
        Prefer those, and fall back to the flat fields when a result has none.
        """
        parts = []
        for passage in obj.get("passages") or []:
            text = passage.get("text") if isinstance(passage, dict) else passage
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
        if parts:
            return "\n\n".join(parts)
        return obj.get("snippet") or obj.get("content") or obj.get("passage") or ""

    def search(self, max_results=10):
        """
        Searches the query
        Returns:

        """
        try:
            # Search the query
            results = self._search(self.query, max_results=max_results)
            sources = results.get("results", [])
            if not sources:
                raise Exception("No results found with Caesar API search.")
            # Normalize the results to GPT Researcher's {href, body} shape.
            search_response = []
            for obj in sources:
                href = obj.get("url") or obj.get("canonical_url") or obj.get("source_url")
                if not href:
                    continue
                search_response.append({"href": href, "body": self._body(obj)})
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response
