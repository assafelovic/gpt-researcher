from __future__ import annotations

from typing import Any, ClassVar

import requests


class SemanticScholarSearch:
    """Semantic Scholar API Retriever."""

    BASE_URL: ClassVar[str] = "https://api.semanticscholar.org/graph/v1/paper/search"
    VALID_SORT_CRITERIA: ClassVar[list[str]] = ["relevance", "citationCount", "publicationDate"]

    def __init__(
        self,
        query: str,
        sort: str = "relevance",
    ):
        """Initializes the SemanticScholarSearch class with a query and sort criterion.

        Args:
            query (str): Search query string
            sort (str): Sort criterion ('relevance', 'citationCount', 'publicationDate')
        """
        self.query: str = query
        assert sort in self.VALID_SORT_CRITERIA, "Invalid sort criterion"
        self.sort: str = sort.lower()

    def search(
        self,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """Perform the search on Semantic Scholar and return results.

        Args:
            max_results (int): Maximum number of results to retrieve

        Returns:
            list[dict[str, Any]]: List of dictionaries containing title, href, and body of each paper
        """
        params: dict[str, Any] = {
            "query": self.query,
            "limit": max_results,
            "fields": "title,abstract,url,venue,year,authors,isOpenAccess,openAccessPdf",
            "sort": self.sort,
        }

        try:
            response: requests.Response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"An error occurred while accessing Semantic Scholar API: {e.__class__.__name__}: {e}")
            return []

        results: list[dict[str, Any]] = response.json().get("data", [])
        search_result_list: list[dict[str, Any]] = []

        for result in results:
            if result.get("isOpenAccess") and result.get("openAccessPdf"):
                search_result_list.append(
                    {
                        "title": result.get("title", "No Title"),
                        "href": result.get("openAccessPdf", {}).get("url", "No URL"),
                        "body": result.get("abstract", "Abstract not available"),
                    }
                )

        return search_result_list
