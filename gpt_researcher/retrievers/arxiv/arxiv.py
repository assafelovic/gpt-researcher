from __future__ import annotations

from typing import Any, cast

import arxiv


class ArxivSearch:
    """Arxiv API Retriever."""

    def __init__(
        self,
        query: str,
        sort: str = "Relevance",
        query_domains: list[str] | None = None,
        *_: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        self.arxiv: arxiv.Client = arxiv.Client()
        self.query: str = query
        assert sort in ["Relevance", "SubmittedDate"], "Invalid sort criterion"
        self.sort: arxiv.SortCriterion = (
            arxiv.SortCriterion.SubmittedDate
            if sort == "SubmittedDate"
            else arxiv.SortCriterion.Relevance
        )
        # Extract config from kwargs if provided
        self.query_domains: list[str] | None = query_domains

    def search(
        self,
        max_results: int | None = None,
    ) -> list[dict[str, Any]]:
        """Performs the search

        Args:
            query: The query to search for.
            max_results: The maximum number of results to return.

        Returns:
            A list of dictionaries containing the search results.
        """
        # Use the provided max_results, or get it from config, or use default
        if max_results is None:
            if self.config and hasattr(self.config, "MAX_SOURCES"):
                max_results = self.config.MAX_SOURCES
            else:
                max_results = 5  # Default fallback
                
        arxiv_results: list[arxiv.Result] = list(
            cast(arxiv, self.arxiv).Search(
                query=self.query,
                id_list=[],
                max_results=max_results,
                sort_by=self.sort,
                sort_order=arxiv.SortOrder.Descending,
            ).results()
        )

        search_result: list[dict[str, Any]] = []

        for result in arxiv_results:
            search_result.append(
                {
                    "title": result.title,
                    "href": result.pdf_url,
                    "body": result.summary,
                }
            )

        return search_result
