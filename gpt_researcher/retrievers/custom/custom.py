from __future__ import annotations

import logging
import os

from typing import Any

import requests

logger: logging.Logger = logging.getLogger(__name__)


class CustomRetriever:
    """Custom API Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        *args: Any,  # provided for compatibility with other retrievers
        **kwargs: Any,  # provided for compatibility with other retrievers
    ):
        self.endpoint: str | None = os.getenv("RETRIEVER_ENDPOINT")
        if not self.endpoint:
            raise ValueError("RETRIEVER_ENDPOINT environment variable not set")

        self.params: dict[str, Any] = self._populate_params()
        self.query: str = query
        self.query_domains: list[str] | None = query_domains

    def _populate_params(self) -> dict[str, Any]:
        """Populates parameters from environment variables prefixed with 'RETRIEVER_ARG_'."""
        return {key[len("RETRIEVER_ARG_") :].lower(): value for key, value in os.environ.items() if key.startswith("RETRIEVER_ARG_")}

    def search(
        self,
        max_results: int = 5,
    ) -> list[dict[str, Any]] | None:
        """Performs the search using the custom retriever endpoint.

        Args:
        ----
            max_results: Maximum number of results to return (not currently used)

        Returns:
        -------
            JSON response in the format:
            [
              {
                "url": "http://example.com/page1",
                "raw_content": "Content of page 1"
              },
              {
                "url": "http://example.com/page2",
                "raw_content": "Content of page 2"
              }
            ]
        """
        assert self.endpoint is not None
        try:
            response: requests.Response = requests.get(
                self.endpoint,
                params={**self.params, "query": self.query},
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.exception(f"Failed to retrieve search results: {e.__class__.__name__}: {e}")
            return None
        else:
            return list(response.json())[:max_results]
