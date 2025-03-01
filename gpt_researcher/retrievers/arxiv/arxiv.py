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
        *args: Any,  # provided for compatibility with other retrievers
        **kwargs: Any,  # provided for compatibility with other retrievers
    ):
        self.arxiv: arxiv.Client = arxiv.Client()
        self.query: str = query
        assert sort in ["Relevance", "SubmittedDate"], "Invalid sort criterion"
        self.sort: arxiv.SortCriterion = (
            arxiv.SortCriterion.SubmittedDate
            if sort == "SubmittedDate"
            else arxiv.SortCriterion.Relevance
        )

    def search(
        self,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Performs the search

        Args:
            query: The query to search for.
            max_results: The maximum number of results to return.

        Returns:
            A list of dictionaries containing the search results.
        """
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
