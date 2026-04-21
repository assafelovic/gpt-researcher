import os
from typing import Dict, List, Optional

import requests


class OpenAlexSearch:
    """
    OpenAlex API Retriever.

    OpenAlex (https://openalex.org) is an open catalog of scholarly works.
    No API key is required for default usage.

    Optional environment variables:
    - OPENALEX_EMAIL: adds the caller to OpenAlex's polite pool for more
      predictable rate limits (recommended for production use).
    - OPENALEX_API_KEY: authenticated access with higher rate limits
      (register for free at https://openalex.org/).

    See https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication
    for current rate limit details.
    """

    BASE_URL = "https://api.openalex.org/works"
    VALID_SORT_CRITERIA = [
        "relevance_score:desc",
        "cited_by_count:desc",
        "publication_date:desc",
    ]

    def __init__(self, query: str, sort: str = "relevance_score:desc", query_domains=None):
        """
        Initialize the OpenAlexSearch class with a query and sort criterion.

        :param query: Search query string.
        :param sort: Sort criterion. One of VALID_SORT_CRITERIA.
        """
        self.query = query
        assert sort in self.VALID_SORT_CRITERIA, f"Invalid sort criterion: {sort}"
        self.sort = sort
        self.email: Optional[str] = os.environ.get("OPENALEX_EMAIL")
        self.api_key: Optional[str] = os.environ.get("OPENALEX_API_KEY")

    def search(self, max_results: int = 20) -> List[Dict[str, str]]:
        """
        Perform the search on OpenAlex and return results.

        :param max_results: Maximum number of results to retrieve (capped at 25 per request).
        :return: List of dictionaries containing title, href, and body of each work.
        """
        params = {
            "search": self.query,
            "per_page": min(max_results, 25),
            "sort": self.sort,
        }
        if self.email:
            params["mailto"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"An error occurred while accessing OpenAlex API: {e}")
            return []

        results = response.json().get("results", [])
        search_result = []
        for result in results:
            title = result.get("title") or "No Title"
            href = self._pick_href(result)
            body = self._reconstruct_abstract(result.get("abstract_inverted_index"))

            if href:
                search_result.append(
                    {
                        "title": title,
                        "href": href,
                        "body": body or "Abstract not available",
                    }
                )

        return search_result

    @staticmethod
    def _pick_href(result: dict) -> Optional[str]:
        """
        Prefer the open-access PDF URL, then the landing page URL from
        primary_location, then the OpenAlex work URL as fallback.
        """
        oa_location = result.get("best_oa_location") or {}
        pdf_url = oa_location.get("pdf_url")
        if pdf_url:
            return pdf_url

        primary = result.get("primary_location") or {}
        landing = primary.get("landing_page_url")
        if landing:
            return landing

        return result.get("id")

    @staticmethod
    def _reconstruct_abstract(inverted: Optional[dict]) -> Optional[str]:
        """
        OpenAlex returns abstracts as an inverted index (word -> positions).
        Reconstruct the original text.
        """
        if not inverted:
            return None
        positions: List[tuple] = []
        for word, indexes in inverted.items():
            for i in indexes:
                positions.append((i, word))
        positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in positions)
