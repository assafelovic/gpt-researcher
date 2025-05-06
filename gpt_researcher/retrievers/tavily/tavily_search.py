# Tavily API Retriever

# libraries
import os
from typing import Literal, Sequence, Optional
import requests
import json


class TavilySearch():
    """
    Tavily API Retriever
    """

    def __init__(self, query, headers=None, topic="general"):
        """
        Initializes the TavilySearch object
        Args:
            query:
        """
        self.query = query
        self.headers = headers or {}
        self.topic = topic
        self.base_url = "https://api.tavily.com/search"
        self.api_key = self.get_api_key()
        self.headers = {
            "Content-Type": "application/json",
        }

    def get_api_key(self):
        """
        Gets the Tavily API key
        Returns:

        """
        api_key = self.headers.get("tavily_api_key")
        if not api_key:
            try:
                api_key = os.environ["TAVILY_API_KEY"]
            except KeyError:
                raise Exception(
                    "Tavily API key not found. Please set the TAVILY_API_KEY environment variable.")
        return api_key

    def _search(self,
                query: str,
                search_depth: Literal["basic", "advanced"] = "basic",
                topic: str = "general",
                days: int = 2,
                max_results: int = 5,
                include_domains: Sequence[str] = None,
                exclude_domains: Sequence[str] = None,
                include_answer: bool = False,
                include_raw_content: bool = False,
                include_images: bool = False,
                use_cache: bool = True,
                ) -> dict:
        """
        Internal search method to send the request to the API.
        """

        data = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "days": days,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "max_results": max_results,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_images": include_images,
            "api_key": self.api_key,
            "use_cache": use_cache,
        }

        response = requests.post(self.base_url, data=json.dumps(
            data), headers=self.headers, timeout=100)

        if response.status_code == 200:
            return response.json()
        else:
            # Raises a HTTPError if the HTTP request returned an unsuccessful status code
            response.raise_for_status()

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        try:
            # Search the query
            results = self._search(
                self.query, search_depth="basic", max_results=max_results, topic=self.topic)
            sources = results.get("results", [])
            if not sources:
                raise Exception("No results found with Tavily API search.")
            # Return the results
            search_response = [{"href": obj["url"],
                                "body": obj["content"]} for obj in sources]
        except Exception as e:
            print(
                f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response
