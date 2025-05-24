# Bing Search Retriever

# libraries
import os
from typing import Any
import requests
import json
import logging


class BingSearch():

    """Bing Search Retriever."""

    def __init__(self, query: str):
        """Initializes the BingSearch object.

        Args:
            query (str): The query to search for.
        """
        self.query: str = query
        self.api_key: str = self.get_api_key()
        self.logger: logging.Logger = logging.getLogger(__name__)

    def get_api_key(self) -> str:
        """Gets the Bing API key.

        Returns:
            str: The Bing API key.
        """
        try:
            api_key: str = os.environ["BING_API_KEY"]
        except KeyError:
            raise Exception(
                "Bing API key not found. Please set the BING_API_KEY environment variable.")
        return api_key

    def search(self, max_results: int = 7) -> list[dict[str, Any]]:
        """Searches the query.

        Args:
            max_results (int): The maximum number of results to return.

        Returns:
            list[dict[str, Any]]: The search results.
        """
        print(f"Searching with query '{self.query}'...")
        """Useful for general internet search queries using the Bing API."""

        # Search the query
        url: str = "https://api.bing.microsoft.com/v7.0/search"

        headers: dict[str, str] = {
            'Ocp-Apim-Subscription-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        params: dict[str, Any] = {
            "responseFilter": "Webpages",
            "q": self.query,
            "count": max_results,
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
            "safeSearch": "Strict"
        }

        resp: requests.Response | None = requests.get(url, headers=headers, params=params)

        # Preprocess the results
        if resp is None:
            return []
        try:
            search_results: dict[str, Any] = json.loads(resp.text)
            results: list[dict[str, Any]] = search_results["webPages"]["value"]
        except Exception as e:
            self.logger.error(
                f"Error parsing Bing search results: {e.__class__.__name__}: {e}. Resulting in empty response.")
            return []
        if search_results is None:
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
