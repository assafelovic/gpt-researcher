"""Tavily API Retriever."""

# libraries
from __future__ import annotations

import json
import os

from typing import Any, Literal, Sequence

import requests


class TavilySearch():

    """Tavily API Retriever."""

    def __init__(
        self,
        query: str,
        headers: dict[str, Any] | None = None,
        topic: str = "general",
    ):
        """Initializes the TavilySearch object.

        Args:
            query (str): The query to search for.
            headers (dict[str, Any], optional): The headers to use for the request.
            topic (str, optional): The topic to search for.
        """
        self.query: str = query
        self.topic: str = topic
        self.base_url: str = "https://api.tavily.com/search"
        self.api_key: str = self.get_api_key()
        self.headers: dict[str, Any] = {
            "Content-Type": "application/json",
            **(headers or {}),
        }

    def get_api_key(self) -> str:
        """Gets the Tavily API key.

        Returns:
            str: The Tavily API key.
        """
        api_key: str | None = self.headers.get("tavily_api_key")
        if not api_key or not api_key.strip():
            api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key or not api_key.strip():
            raise Exception("Tavily API key not found. Please set the TAVILY_API_KEY environment variable.")
        return api_key

    def _search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = "basic",
        topic: str = "general",
        days: int = 2,
        max_results: int = 5,
        include_domains: Sequence[str] | None = None,
        exclude_domains: Sequence[str] | None = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Internal search method to send the request to the API.

        Args:
            query (str): The query to search for.
            search_depth (Literal["basic", "advanced"], optional): The search depth.
            topic (str, optional): The topic to search for.
            days (int, optional): The number of days to search for.
            max_results (int, optional): The maximum number of results to return.
            include_domains (Sequence[str], optional): The domains to include in the search.
            exclude_domains (Sequence[str], optional): The domains to exclude from the search.
            include_answer (bool, optional): Whether to include the answer in the search.
            include_raw_content (bool, optional): Whether to include the raw content in the search.
            include_images (bool, optional): Whether to include images in the search.
            use_cache (bool, optional): Whether to use the cache.

        Returns:
            dict[str, Any]: The search results.
        """

        data: dict[str, Any] = {
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

        response: requests.Response = requests.post(
            self.base_url,
            data=json.dumps(data),
            headers=self.headers,
            timeout=100,
        )

        # Raises a HTTPError if the HTTP request returned an unsuccessful status code
        response.raise_for_status()
        return response.json()

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
        try:
            # Search the query
            results: dict[str, Any] = self._search(
                self.query,
                search_depth="basic",
                max_results=max_results,
                topic=self.topic,
            )
            sources: list[dict[str, Any]] = results.get("results", [])
            if not sources:
                raise Exception("No results found with Tavily API search.")
            # Return the results
            search_response: list[dict[str, Any]] = [
                {
                    "href": obj["url"],
                    "body": obj["content"],
                }
                for obj in sources
            ]
        except Exception as e:
            print(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")
            search_response: list[dict[str, Any]] = []
        return search_response
