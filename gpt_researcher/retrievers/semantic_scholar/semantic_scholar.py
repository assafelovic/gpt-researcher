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
        self.sort = sort.lower()

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

        payload = response.json()
        if not isinstance(payload, dict):
            return []
        results = payload.get("data") or []
        if not isinstance(results, list):
            return []

        search_result = []
        for result in results:
            if not isinstance(result, dict):
                continue
            pdf = result.get("openAccessPdf")
            if not (result.get("isOpenAccess") and isinstance(pdf, dict)):
                continue
            href = pdf.get("url") or ""
            if not href:
                continue
            search_result.append(
                {
                    "title": result.get("title") or "No Title",
                    "href": href,
                    "body": result.get("abstract") or "Abstract not available",
                }
            )

        return search_result
