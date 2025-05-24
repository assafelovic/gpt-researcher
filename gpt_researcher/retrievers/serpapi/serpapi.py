# SerpApi Retriever

# libraries
from __future__ import annotations

import os
import urllib.parse

from typing import Any

import requests



    """SerpApi Retriever."""

    def __init__(self, query: str):
        """Initializes the SerpApiSearch object.

class SerpApiSearch():
        Args:
            query (str): The query to search for.
        """
        self.query: str = query
        self.api_key: str = self.get_api_key()

    def get_api_key(self) -> str:
        """Gets the SerpApi API key.

        Returns:
            str: The SerpApi API key.
        """
        try:
            api_key: str = os.environ.get("SERPAPI_API_KEY")
            if not api_key or not api_key.strip():
                raise KeyError
        except KeyError:
            raise Exception("SerpApi API key not found. Please set the SERPAPI_API_KEY environment variable. " "You can get a key at https://serpapi.com/")
        return api_key

    def search(self, max_results: int = 7) -> list[dict[str, Any]]:
        """Searches the query.

        Returns:
            list[dict[str, Any]]: The search results.
        """
        print(f"SerpApiSearch: Searching with query {self.query}...")
        """Useful for general internet search queries using SerpApi."""

        # Search the query (see https://serpapi.dev/playground for the format)
        url: str = "https://serpapi.com/search.json"
        params: dict[str, Any] = {"q": self.query, "api_key": self.api_key}
        encoded_url: str = url + "?" + urllib.parse.urlencode(params)
        search_response_list: list[dict[str, Any]] = []
        try:
            response: requests.Response = requests.get(encoded_url, timeout=10)
            if response.status_code == 200:
                search_results: dict[str, Any] = response.json()
                if search_results:
                    results: list[dict[str, Any]] = search_results["organic_results"]
                    results_processed: int = 0
                    for result in results:
                        # skip youtube results
                        if "youtube.com" in str(result.get("link", "")).casefold():
                            continue
                        if results_processed >= max_results:
                            break
                        search_result: dict[str, Any] = {
                            "title": result["title"],
                            "href": result["link"],
                            "body": result["snippet"],
                        }
                        search_response_list.append(search_result)
                        results_processed += 1
        except Exception as e:
            print(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")

        return search_response_list
