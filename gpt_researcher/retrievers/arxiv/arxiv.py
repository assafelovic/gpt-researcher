from __future__ import annotations

import arxiv


class ArxivSearch:
    """Arxiv API Retriever."""

    def __init__(
        self,
        query: str,
        sort: str = "Relevance",
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
    ) -> list[dict[str, str]]:
        """Performs the search."""

        arxiv_gen = list(
            arxiv.Client().results(
                arxiv.Search(
                    query=self.query,  # +
                    max_results=max_results,
                    sort_by=self.sort,
                )
            )
        )

        search_result_list: list[dict[str, str]] = []

        for result in arxiv_gen:
            search_result_list.append(
                {
                    "title": result.title,
                    "href": result.pdf_url or "",
                    "body": result.summary,
                }
            )

        return search_result_list
