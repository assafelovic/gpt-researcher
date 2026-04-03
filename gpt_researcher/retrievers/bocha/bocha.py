# BoCha Search Retriever

# libraries
import os
import requests
import json
import logging


class BoChaSearch():
    """
    BoCha Search Retriever
    """

    def __init__(self, query, query_domains=None):
        """
        Initializes the BoChaSearch object
        Args:
            query:
        """
        self.query = query
        self.query_domains = query_domains or None
        self.api_key = self.get_api_key()
        self.logger = logging.getLogger(__name__)

    def get_api_key(self):
        """
        Gets the BoCha API key
        Returns:
            str: The API key
        """
        try:
            api_key = os.environ["BOCHA_API_KEY"]
        except KeyError:
            raise Exception(
                "BoCha API key not found. Please set the BOCHA_API_KEY environment variable.")
        return api_key

    def search(self, max_results=7) -> list[dict[str]]:
        """
        Searches the query
        Returns:
            list: List of search results with title, href and body
        """
        url = 'https://api.bochaai.com/v1/web-search'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "query": self.query,
            "freshness": "noLimit",
            "summary": True,
            "count": max_results
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code != 200:
                self.logger.error(
                    f"BoCha search failed with status {response.status_code}: {response.text}")
                return []

            json_response = response.json()
            results = json_response.get("data", {}).get("webPages", {}).get("value", [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"BoCha search request failed: {e}")
            return []
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error parsing BoCha search response: {e}")
            return []

        search_results = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            search_result = {
                "title": result.get("name", ""),
                "href": result.get("url", ""),
                "body": result.get("snippet", ""),
            }
            search_results.append(search_result)

        return search_results