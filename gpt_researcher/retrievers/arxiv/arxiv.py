from __future__ import annotations

from typing import Any

import arxiv



    """Arxiv API Retriever."""

class ArxivSearch:
    def __init__(self, query: str, sort: str = "Relevance"):
        """Initializes the ArxivSearch object.

        Args:
            query (str): The query to search for.
            sort (str): The sort criterion.
        """
        self.arxiv: arxiv.Client = arxiv.Client()
        self.query: str = query
        assert sort in ["Relevance", "SubmittedDate"], "Invalid sort criterion"
        self.sort: arxiv.SortCriterion | arxiv.SortCriterion = (
            arxiv.SortCriterion.SubmittedDate
            if sort == "SubmittedDate"
            else arxiv.SortCriterion.Relevance
        )  # pyright: ignore[reportOptionalMemberAccess]

    def search(self, max_results: int = 5) -> list[dict[str, Any]]:
        """Performs the search.

        Args:
            max_results (int): The maximum number of results to return.

        Returns:
            list[dict[str, Any]]: The search results.
        """

        arxiv_gen: list[arxiv.Result] = list(
            self.arxiv.results(
                self.arxiv.Search(
                    query=self.query,
                    max_results=max_results,
                    sort_by=self.sort,
                )
            )
        )

        search_result: list[dict[str, Any]] = []

        for result in arxiv_gen:
            search_result.append(
                {
                    "title": result.title,
                    "href": result.pdf_url,
                    "body": result.summary,
                }
            )

        return search_result
