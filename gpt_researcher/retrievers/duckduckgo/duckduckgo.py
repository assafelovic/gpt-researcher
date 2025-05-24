from __future__ import annotations

from typing import Any

from gpt_researcher.retrievers.utils import check_pkg


class Duckduckgo:
    """Duckduckgo API Retriever."""

    def __init__(self, query: str):
        check_pkg("duckduckgo_search")
        from duckduckgo_search import DDGS

        self.ddg: DDGS = DDGS()
        self.query: str = query

    def search(self, max_results: int = 5) -> list[dict[str, Any]]:
        """Performs the search.

        Args:
            query (str): The query to search for.
            max_results (int): The maximum number of results to return.

        Returns:
            list[dict[str, Any]]: The search results.
        """
        try:
            search_response: list[dict[str, Any]] = self.ddg.text(self.query, region="wt-wt", max_results=max_results)
        except Exception as e:
            print(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")
            search_response: list[dict[str, Any]] = []
        return search_response
