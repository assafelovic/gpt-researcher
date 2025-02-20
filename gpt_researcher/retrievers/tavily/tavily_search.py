# Tavily API Retriever

# libraries
from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from logging import Logger
    from typing import Any, ClassVar, Literal, Sequence

    from requests import Response


class TavilySearch:
    """Tavily API Retriever."""

    logger: ClassVar[Logger] = logging.getLogger(__name__)

    def __init__(
        self,
        query: str,
        headers: dict[str, Any] | None = None,
        topic: str = "general",
    ):
        """Initializes the TavilySearch object."""
        self.query: str = query
        self.headers: dict[str, Any] = headers or {}
        self.topic: str = topic
        self.base_url: str = "https://api.tavily.com/search"
        self.api_key: str = self.get_api_key()
        self.headers: dict[str, Any] = {"Content-Type": "application/json"}

    def get_api_key(self) -> str:
        """Gets the Tavily API key.

        Returns:
            str: The Tavily API key.
        """
        api_key: str = self.headers.get("tavily_api_key", "")
        if not api_key:
            try:
                api_key = os.environ["TAVILY_API_KEY"]
            except KeyError:
                raise Exception(
                    "Tavily API key not found. Please set the TAVILY_API_KEY environment variable."
                )
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
    ) -> dict[str, Any] | None:
        """Internal search method to send the request to the API."""

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

        response: Response = requests.post(
            self.base_url,
            data=json.dumps(data),
            headers=self.headers,
            timeout=100,
        )

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
            results: dict[str, Any] | None = self._search(
                self.query,
                search_depth="basic",
                max_results=max_results,
                topic=self.topic,
            )
            if results is None:
                raise Exception("No results found with Tavily API search.")
            sources: list[dict[str, Any]] = results.get("results", [])
            if not sources:
                raise Exception("No results found with Tavily API search.")
            # Return the results
            search_response: list[dict[str, Any]] = [
                {"href": obj["url"], "body": obj["content"]} for obj in sources
            ]
        except Exception as e:
            self.logger.exception("Failed fetching sources. Resulting in empty response.")
            search_response: list[dict[str, Any]] = []
        return search_response
