"""Nimble Search API retriever for GPT Researcher.

This module provides the NimbleSearch class for performing web searches
using the Nimble Search API (https://docs.nimbleway.com/nimble-sdk/web-tools/search).
"""

import os
from typing import Optional, Sequence

import requests


class NimbleSearch:
    """
    Nimble Search API Retriever
    """

    def __init__(self, query, query_domains=None):
        """
        Initializes the NimbleSearch object.

        Args:
            query (str): The search query string.
            query_domains (list, optional): List of domains to restrict the search to. Defaults to None.
        """
        self.query = query
        self.query_domains = query_domains or None
        self.base_url = "https://sdk.nimbleway.com/v1/search"
        self.api_key = self.get_api_key()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_api_key(self):
        """
        Gets the Nimble API key from the environment.

        Returns:
            str: The API key, or "" if unset.
        """
        try:
            api_key = os.environ["NIMBLE_API_KEY"]
        except KeyError:
            print(
                "Nimble API key not found, set to blank. If you need this retriever, "
                "please set the NIMBLE_API_KEY environment variable."
            )
            return ""
        return api_key

    def _search(
        self,
        query: str,
        max_results: int = 10,
        include_domains: Optional[Sequence[str]] = None,
    ) -> dict:
        """
        Internal search method that sends the request to the Nimble Search API.
        """
        payload = {
            "query": query,
            "max_results": max_results,
        }
        if include_domains:
            payload["include_domains"] = list(include_domains)

        response = requests.post(
            self.base_url, json=payload, headers=self.headers, timeout=100
        )
        response.raise_for_status()
        return response.json()

    def search(self, max_results=10):
        """
        Searches the query using the Nimble Search API.

        Returns:
            list[dict]: A list of {"href", "body", "title"} result dicts,
            or an empty list on failure.
        """
        try:
            results = self._search(
                self.query,
                max_results=max_results,
                include_domains=self.query_domains,
            )
            sources = results.get("results", [])
            if not sources:
                raise Exception("No results found with Nimble Search API.")
            # In the default (lite) search depth, `content` is absent and the
            # snippet text is carried by `description`.
            search_response = [
                {
                    "href": obj.get("url"),
                    "body": obj.get("content") or obj.get("description") or "",
                    "title": obj.get("title", ""),
                }
                for obj in sources
                if obj.get("url")
            ]
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response
