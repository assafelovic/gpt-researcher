from __future__ import annotations

import logging
import os
import urllib.parse
from typing import Any, Optional

import requests

class SearchApiSearch:
    """SearchApi Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        *_: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        """Initializes the SearchApiSearch object.

        Args:
            query (str): The query to search for.
            query_domains (list[str] | None): The domains to search for.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.query: str = query
        self.query_domains: list[str] = [] if query_domains is None else query_domains
        self.api_key: str = self.get_api_key()
        self.config = kwargs.get("config") if kwargs else None

    def get_api_key(self) -> str:
        """Gets the SearchApi API key.

        Returns:
            str: The SearchApi API key.
        """
        try:
            api_key: str = os.environ["SEARCHAPI_API_KEY"]
        except KeyError:
            raise Exception(
                "SearchApi key not found. Please set the SEARCHAPI_API_KEY environment variable. You can get a key at https://www.searchapi.io/"
            )
        return api_key

    def search(
        self,
        max_results: Optional[int] = None,
    ) -> list[dict[str, str]]:
        """Searches the query.

        Useful for general internet search queries using SearchApi.

        Returns:
            list[dict[str, str]]: The search results.
        """
        # Use the provided max_results, or get it from config, or use default
        if max_results is None:
            if self.config and hasattr(self.config, "MAX_SOURCES"):
                max_results = self.config.MAX_SOURCES
                assert max_results is not None
            else:
                max_results = 7  # Default fallback
            
        logging.info(f"SearchApiSearch: Searching with query {self.query}...")

        url: str = "https://www.searchapi.io/api/v1/search"
        params: dict[str, str] = {
            "q": self.query,
            "engine": "google",
        }

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-SearchApi-Source": "gpt-researcher",
        }

        encoded_url: str = url + "?" + urllib.parse.urlencode(params)
        search_response: list[dict[str, str]] = []

        try:
            response = requests.get(encoded_url, headers=headers, timeout=20)
            if response.status_code != 200:
                return []
            search_results: dict[str, list[dict[str, str]]] = response.json()
            if not search_results:
                return []
            results: list[dict[str, str]] = search_results["organic_results"]
            results_processed: int = 0
            for result in results:
                # skip youtube results
                if "youtube.com" in result["link"]:
                    continue
                if results_processed >= max_results:
                    break
                search_result: dict[str, str] = {
                    "title": result["title"],
                    "href": result["link"],
                    "body": result["snippet"],
                }
                search_response.append(search_result)
                results_processed += 1

        except Exception as e:
            logging.exception(
                f"Failed fetching sources. Resulting in empty response.  {e.__class__.__name__}: {e}"
            )
            search_response = []

        return search_response