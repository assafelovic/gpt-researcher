from typing import Dict, List

import requests


class SemanticScholarSearch:
    """
    Semantic Scholar API Retriever
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    VALID_SORT_CRITERIA = ["relevance", "citationCount", "publicationDate"]

    def __init__(self, query: str, sort: str = "relevance", query_domains=None):
        """
        Initialize the SemanticScholarSearch class with a query and sort criterion.

        :param query: Search query string
        :param sort: Sort criterion ('relevance', 'citationCount', 'publicationDate')
        """
        self.query = query
        assert sort in self.VALID_SORT_CRITERIA, "Invalid sort criterion"
        # Keep API sort casing (citationCount / publicationDate); only validate above.
        self.sort = sort

    def search(self, max_results: int = 20) -> List[Dict[str, str]]:
        """
        Perform the search on Semantic Scholar and return results.

        :param max_results: Maximum number of results to retrieve
        :return: List of dictionaries containing title, href, and body of each paper
        """
        params = {
            "query": self.query,
            "limit": max_results,
            "fields": "title,abstract,url,venue,year,authors,isOpenAccess,openAccessPdf",
            "sort": self.sort,
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"An error occurred while accessing Semantic Scholar API: {e}")
            return []

        try:
            payload = response.json()
        except ValueError as e:
            print(f"An error occurred while decoding Semantic Scholar JSON: {e}")
            return []

        if not isinstance(payload, dict):
            return []

        results = payload.get("data", [])
        if not isinstance(results, list):
            return []

        search_result = []

        for result in results:
            if not isinstance(result, dict):
                continue
            if not result.get("isOpenAccess"):
                continue
            open_access_pdf = result.get("openAccessPdf")
            # API may return null, a URL string, or an object with url.
            if isinstance(open_access_pdf, dict):
                href = open_access_pdf.get("url") or ""
            elif isinstance(open_access_pdf, str):
                href = open_access_pdf
            else:
                continue
            if not href:
                continue
            search_result.append(
                {
                    "title": result.get("title", "No Title"),
                    "href": href,
                    "body": result.get("abstract", "Abstract not available"),
                }
            )

        return search_result
