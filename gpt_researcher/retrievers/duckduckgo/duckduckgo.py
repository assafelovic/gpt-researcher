from itertools import islice
from ..utils import check_pkg


class Duckduckgo:
    """
    Duckduckgo API Retriever
    """
    def __init__(self, query, query_domains=None):
        check_pkg('ddgs')
        from ddgs import DDGS
        self.ddg = DDGS()
        self.query = query
        self.query_domains = query_domains or None

    def _build_query(self):
        """Build the search query, optionally filtering by domain."""
        query = self.query
        if self.query_domains:
            domain_query = " OR ".join([f"site:{domain}" for domain in self.query_domains])
            query = f"({domain_query}) {query}"
        return query

    def search(self, max_results=5):
        """
        Performs the search
        :param query:
        :param max_results:
        :return:
        """
        try:
            search_query = self._build_query()
            search_response = self.ddg.text(search_query, region='wt-wt', max_results=max_results)
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response
