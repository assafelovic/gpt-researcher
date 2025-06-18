# Bing Search Retriever

# libraries
from __future__ import annotations

import json
import logging
import os

from typing import Any

import requests

from gpt_researcher.retrievers.retriever_abc import RetrieverABC
class BingSearch(RetrieverABC):
    """Bing Search Retriever."""

    def __init__(self, query: str, query_domains: list[str] | None = None):
        """Initializes the BingSearch object.

        Args:
            query:
        """
        self.query = query
        self.query_domains = query_domains or None
        self.api_key = self.get_api_key()
        self.logger = logging.getLogger(__name__)

    def get_api_key(self) -> str:
        """Gets the Bing API key.

        Returns:

        """
        try:
            api_key = os.environ["BING_API_KEY"]
        except:
            raise Exception(
                "Bing API key not found. Please set the BING_API_KEY environment variable.")
        return api_key

    def search(self, max_results: int = 7) -> list[dict[str, Any]]:
        """Searches the query.

        Returns:
            list[dict[str, Any]]: A list of dictionaries containing the search results.
        """
        print(f"Searching with query {self.query}...".format(self.query))
        """Useful for general internet search queries using the Bing API."""

        # Search the query
        url: str = "https://api.bing.microsoft.com/v7.0/search"

        headers: dict[str, str] = {
            'Ocp-Apim-Subscription-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        # TODO: Add support for query domains
        params: dict[str, Any] = {
            "responseFilter": "Webpages",
            "q": self.query,
            "count": max_results,
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
            "safeSearch": "Strict"
        }

        resp: requests.Response = requests.get(url, headers=headers, params=params)

        # Preprocess the results
        if resp is None:
            return []
        try:
            search_results: dict[str, Any] = json.loads(resp.text)
            results: list[dict[str, Any]] = search_results["webPages"]["value"]
        except Exception as e:
            self.logger.error(f"Error parsing Bing search results: {e.__class__.__name__}: {e}. Resulting in empty response.")
            return []
        if not search_results:
            self.logger.warning(f"No search results found for query: {self.query}")
            return []
        search_results_list: list[dict[str, Any]] = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in str(result.get("url", "")).casefold():
                continue
            search_result: dict[str, Any] = {
                "title": result.get("name", "No Title"),
                "href": result.get("url", "No URL"),
                "body": result.get("snippet", "No Snippet"),
            }
            search_results_list.append(search_result)

        return search_results_list
