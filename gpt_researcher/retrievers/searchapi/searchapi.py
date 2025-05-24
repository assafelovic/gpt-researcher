# SearchApi Retriever

# libraries
from __future__ import annotations

import os
import urllib.parse

from typing import Any

import requests


class SearchApiSearch:
    """SearchApi Retriever."""

    def __init__(
        self,
        query: str,
    ):
        """Initializes the SearchApiSearch object.

        Args:
            query (str): The query to search for.
        """
        self.query: str = query
        self.api_key: str = self.get_api_key()

    def get_api_key(self) -> str:
        """Gets the SearchApi API key.

        Returns:
            str: The SearchApi API key.
        """
        try:
            api_key: str = os.environ["SEARCHAPI_API_KEY"]
        except KeyError:
            raise Exception("SearchApi key not found. Please set the SEARCHAPI_API_KEY environment variable. " "You can get a key at https://www.searchapi.io/")
        return api_key  # pyright: ignore[reportReturnStatementIssue]

    def search(
        self,
        max_results: int = 7,
    ) -> list[dict[str, Any]]:
        """Searches the query.

        Args:
            max_results (int): The maximum number of results to return.

        Returns:
            list[dict[str, Any]]: The search results.
        """
        print(f"SearchApiSearch: Searching with query {self.query}...")
        """Useful for general internet search queries using SearchApi."""

        url: str = "https://www.searchapi.io/api/v1/search"
        params: dict[str, Any] = {
            "q": self.query,
            "engine": "google",
        }

        headers: dict[str, Any] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-SearchApi-Source": "gpt-researcher",
        }

        encoded_url: str = f"{url}?{urllib.parse.urlencode(params)}"
        search_response: list[dict[str, Any]] = []

        try:
            response: requests.Response = requests.get(encoded_url, headers=headers, timeout=20)
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
                        search_response.append(search_result)
                        results_processed += 1
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")

        return search_response
