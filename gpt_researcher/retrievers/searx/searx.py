from __future__ import annotations

import json
import os

from typing import Any
from urllib.parse import urljoin

import requests

from gpt_researcher.retrievers.retriever_abc import RetrieverABC


class SearxSearch(RetrieverABC):
    """SearxNG API Retriever."""

    def __init__(self, query: str, query_domains: list[str] | None = None):
        """Initializes the SearxSearch object.

        Args:
            query (str): Search query string
            query_domains (list[str] | None): Optional list of domains (not used for SearxNG).
        """
        self.query: str = query
        self.query_domains: list[str] | None = query_domains
        self.base_url: str = self.get_searxng_url()

    def get_searxng_url(self) -> str:
        """Gets the SearxNG instance URL from environment variables.

        Returns:
            str: Base URL of SearxNG instance.
        """
        try:
            base_url: str = os.environ["SEARX_URL"]
            if not base_url.endswith("/"):
                base_url += "/"
            return base_url  # pyright: ignore[reportReturnStatementIssue]
        except KeyError:
            raise Exception("SearxNG URL not found. Please set the SEARX_URL environment variable. " "You can find public instances at https://searx.space/")

    def search(
        self,
        max_results: int = 10,
    ) -> list[dict[str, str]]:
        """Searches the query using SearxNG API.

        Args:
            max_results (int): Maximum number of results to return

        Returns:
            list[dict[str, str]]: List of dictionaries containing search results
        """
        search_url: str = urljoin(self.base_url, "search")

        params: dict[str, str] = {
            # The search query.
            "q": self.query,
            # Output format of results. Format needs to be activated in searxng config.
            "format": "json",
        }

        try:
            response: requests.Response = requests.get(search_url, params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            results: dict[str, Any] = response.json()

            # Normalize results to match the expected format
            search_response: list[dict[str, str]] = []
            for result in results.get("results", [])[:max_results]:
                search_response.append(
                    {
                        "href": result.get("url", ""),
                        "body": result.get("content", ""),
                    }
                )

            return search_response

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error querying SearxNG: {e.__class__.__name__}: {e}")
        except json.JSONDecodeError:
            raise Exception("Error parsing SearxNG response")
