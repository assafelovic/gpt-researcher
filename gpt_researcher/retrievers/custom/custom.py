from __future__ import annotations

import os

from typing import Any

import requests


class CustomRetriever:
    """Custom API Retriever."""

    def __init__(self, query: str):
        self.endpoint: str = os.getenv("RETRIEVER_ENDPOINT") or ""
        if not self.endpoint or not self.endpoint.strip():
            raise ValueError("RETRIEVER_ENDPOINT environment variable not set")

        self.params: dict[str, Any] = self._populate_params()
        self.query: str = query

    def _populate_params(self) -> dict[str, Any]:
        """Populates parameters from environment variables prefixed with 'RETRIEVER_ARG_'."""
        return {key[len("RETRIEVER_ARG_") :].lower(): value for key, value in os.environ.items() if key.startswith("RETRIEVER_ARG_")}

    def search(self, max_results: int = 5) -> list[dict[str, Any]]:
        """Performs the search using the custom retriever endpoint.

        Args:
            max_results (int): Maximum number of results to return (not currently used)

        Returns:
            list[dict[str, Any]]: JSON response in the format:
            [
                {
                    "url": "http://example.com/page1",
                    "raw_content": "Content of page 1",
                },
                {
                    "url": "http://example.com/page2",
                    "raw_content": "Content of page 2",
                },
            ]
        """
        try:
            response: requests.Response = requests.get(self.endpoint, params={**self.params, "query": self.query})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve search results: {e.__class__.__name__}: {e}")
            return []
