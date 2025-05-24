# Google Search API Retriever

# libraries
from __future__ import annotations

import json
import os

from typing import Any

import requests


class GoogleSearch:
    """Google API Retriever."""

    def __init__(
        self,
        query: str,
        headers: dict[str, Any] | None = None,
    ):
        """Initializes the GoogleSearch object.

        Args:
            query (str): The query to search for.
            headers (dict[str, Any], optional): The headers to use for the request.
        """
        self.query: str = query
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.api_key: str = self.headers.get("google_api_key") or self.get_api_key()  # Use the passed api_key or fallback to environment variable
        self.cx_key: str = self.headers.get("google_cx_key") or self.get_cx_key()  # Use the passed cx_key or fallback to environment variable

    def get_api_key(self) -> str:
        """Gets the Google API key.

        Returns:
            str: The Google API key.
        """

        # Get the API key
        try:
            api_key: str = os.environ["GOOGLE_API_KEY"]
        except KeyError:
            raise Exception(
                "Google API key not found. Please set the GOOGLE_API_KEY environment variable. " "You can get a key at https://developers.google.com/custom-search/v1/overview"
            )
        return api_key  # pyright: ignore[reportReturnStatementIssue]

    def get_cx_key(self) -> str:
        """Gets the Google CX key.

        Returns:
            str: The Google CX key.
        """
        # Get the API key
        try:
            api_key: str = os.environ["GOOGLE_CX_KEY"]
        except KeyError:
            raise Exception(
                "Google CX key not found. Please set the GOOGLE_CX_KEY environment variable. " "You can get a key at https://developers.google.com/custom-search/v1/overview"
            )
        return api_key  # pyright: ignore[reportReturnStatementIssue]

    def search(self, max_results: int = 7) -> list[dict[str, Any]]:
        """Searches the query.

        Args:
            max_results (int): The maximum number of results to return.

        Returns:
            list[dict[str, Any]]: The search results.
        """
        """Useful for general internet search queries using the Google API."""
        print(f"Searching with query {self.query}...")
        url: str = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx_key}&q={self.query}&start=1"
        resp: requests.Response | None = requests.get(url)

        if resp.status_code < 200 or resp.status_code >= 300:
            print("Google search: unexpected response status: ", resp.status_code)

        if resp is None:
            return []
        try:
            search_results: dict[str, Any] = json.loads(resp.text)
        except Exception as e:
            print(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")
            return []
        if not search_results:
            return []

        results: list[dict[str, Any]] = search_results.get("items", [])
        search_results_list: list[dict[str, Any]] = []

        # Normalizing results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in str(result.get("link", "")).casefold():
                continue
            try:
                search_result: dict[str, Any] = {
                    "title": result["title"],
                    "href": result["link"],
                    "body": result["snippet"],
                }
            except Exception as e:
                print(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")
                continue
            search_results_list.append(search_result)

        return search_results_list[:max_results]
