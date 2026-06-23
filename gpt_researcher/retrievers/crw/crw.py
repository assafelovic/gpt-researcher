"""fastCRW API search retriever for GPT Researcher.

This module provides the CRWRetriever class for performing web searches
using fastCRW, a Firecrawl-compatible web data engine (single binary;
self-host or managed cloud).
"""

import json
import os

import requests


class CRWRetriever:
    """
    fastCRW API Retriever
    """

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        """
        Initializes the CRWRetriever object.

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
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        self.query_domains = query_domains or None

    def get_api_key(self, headers):
        """
        Gets the fastCRW API key
        Args:
            headers (dict): The headers passed to the retriever.
        Returns:

        """
        api_key = headers.get("crw_api_key")
        if not api_key:
            try:
                api_key = os.environ["CRW_API_KEY"]
            except KeyError:
                print(
                    "CRW API key not found, set to blank. If you need a retriver, please set the CRW_API_KEY environment variable."
                )
                return ""
        return api_key

    def get_base_url(self, headers):
        """
        Gets the fastCRW base URL, allowing self-host overrides.

        Defaults to the managed cloud at https://fastcrw.com/api. Override with
        the CRW_API_URL environment variable (or the crw_api_url header) to point
        at a self-hosted server.
        Args:
            headers (dict): The headers passed to the retriever.
        Returns:
            The base URL (without a trailing slash).
        """
        base_url = headers.get("crw_api_url") or os.environ.get(
            "CRW_API_URL", "https://fastcrw.com/api"
        )
        return base_url.rstrip("/")

    def _search(self, query: str, max_results: int = 10) -> dict:
        """
        Internal search method to send the request to the API.
        """

        data = {
            "query": query,
            "limit": max_results,
        }

        response = requests.post(
            f"{self.base_url}/v1/search",
            data=json.dumps(data),
            headers=self.headers,
            timeout=100,
        )
        # Raises a HTTPError if the HTTP request returned an unsuccessful status code
        response.raise_for_status()
        results = response.json()
        # fastCRW wraps responses in a {success, error, data} envelope.
        if results.get("success") is False:
            raise Exception(results.get("error", "fastCRW API search failed."))
        return results

    def search(self, max_results=10):
        """
        Searches the query
        Returns:

        """
        try:
            # Search the query
            results = self._search(self.query, max_results=max_results)
            sources = results.get("data", [])
            if not sources:
                raise Exception("No results found with fastCRW API search.")
            # Return the results
            search_response = [
                {
                    "href": obj["url"],
                    "body": obj.get("markdown") or obj.get("description", ""),
                }
                for obj in sources
            ]
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response
