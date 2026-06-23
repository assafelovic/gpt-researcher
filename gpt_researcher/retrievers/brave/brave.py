# Brave Search Retriever

# libraries
import logging
import os

import requests


class BraveSearch:
    """
    Brave Search API Retriever
    """

    def __init__(self, query, query_domains=None):
        """
        Initializes the BraveSearch object
        Args:
            query:
        """
        self.query = query
        self.query_domains = query_domains or None
        self.api_key = self.get_api_key()
        self.logger = logging.getLogger(__name__)

    def get_api_key(self):
        """
        Gets the Brave Search API key
        Returns:

        """
        try:
            api_key = os.environ["BRAVE_API_KEY"]
        except Exception:
            raise Exception(
                "Brave Search API key not found. Please set the BRAVE_API_KEY environment variable."
            )
        return api_key

    def search(self, max_results=7) -> list[dict[str, str]]:
        """
        Searches the query
        Returns:

        """
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using the Brave Search API."""

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        }
        # TODO: Add support for query domains
        params = {
            "q": self.query,
            "count": min(max_results, 20),
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            search_results = response.json()
            results = search_results.get("web", {}).get("results", [])
        except Exception as e:
            self.logger.error(
                f"Error fetching Brave search results: {e}. Resulting in empty response."
            )
            return []

        search_results = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            url = result.get("url")
            if not url:
                continue
            search_result = {
                "title": result.get("title", ""),
                "href": url,
                "body": result.get("description", ""),
            }
            search_results.append(search_result)

        return search_results
