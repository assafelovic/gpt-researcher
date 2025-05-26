from __future__ import annotations

import json
import os

from typing import Any

import requests


class SerperSearch:
    """Google Serper Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
    ):
        """Initializes the SerperSearch object.

        Args:
            query (str): The query to search for.
        """
        self.query: str = query
        self.query_domains: list[str] | None = query_domains or None
        self.api_key: str = self.get_api_key()

    def get_api_key(self) -> str:
        """Gets the Serper API key.

        Returns:
            str: The Serper API key.
        """
        api_key: str | None = os.environ.get("SERPER_API_KEY")
        if not api_key or not api_key.strip():
            raise Exception("Serper API key not found. Please set the SERPER_API_KEY environment variable. You can get a key at https://serper.dev/")
        return api_key

    def search(
        self,
        max_results: int = 7,
    ) -> list[dict[str, Any]]:
        """Searches the query.

        Args:
            max_results (int, optional): The maximum number of results to return.

        Returns:
            list[dict[str, Any]]: The search results.
        """
        print(f"Searching with query {self.query}...")
        """Useful for general internet search queries using the Serp API."""

        # Search the query (see https://serper.dev/playground for the format)
        url: str = "https://google.serper.dev/search"

        headers: dict[str, Any] = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        data: str = json.dumps({"q": self.query, "num": max_results})

        resp: requests.Response = requests.request("POST", url, timeout=10, headers=headers, data=data)

        # Preprocess the results
        if resp.status_code != 200:
            raise Exception(f"Error: {resp.status_code} {resp.text}")
        try:
            search_results: dict[str, Any] = json.loads(resp.text)
        except Exception as e:
            print(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")
            raise Exception(f"Error: {resp.text}")

        results: list[dict[str, Any]] = search_results.get("organic", [])

        # Normalize the results to match the format of the other search APIs
        search_results_list: list[dict[str, Any]] = []
        for result in results:
            # skip youtube results
            if "youtube.com" in str(result.get("link", "")).casefold():
                continue
            search_result: dict[str, Any] = {
                "title": result.get("title", "No Title"),
                "href": result.get("link", "No Link"),
                "body": result.get("snippet", "No Snippet"),
            }
            search_results_list.append(search_result)

        return search_results_list
