# Serply Search Retriever

# libraries
import os
import urllib.parse
import requests


class SerplySearch():
    """
    Serply Search Retriever (Google web results via the Serply SERP API)
    """
    def __init__(self, query, query_domains=None, exclude_sites=None):
        """
        Initializes the SerplySearch object
        Args:
            query (str): The search query string.
            query_domains (list, optional): List of domains to include in the search. Defaults to None.
            exclude_sites (list, optional): List of sites to exclude from search results. Defaults to None.
        """
        self.query = query
        self.query_domains = query_domains or None
        self.exclude_sites = exclude_sites or self._get_exclude_sites_from_env()
        self.api_key = self.get_api_key()

    def _get_exclude_sites_from_env(self):
        """
        Gets the list of sites to exclude from environment variables
        Returns:
            list: List of sites to exclude
        """
        exclude_sites_env = os.getenv("SERPLY_EXCLUDE_SITES", "")
        if exclude_sites_env:
            return [site.strip() for site in exclude_sites_env.split(",") if site.strip()]
        return []

    def get_api_key(self):
        """
        Gets the Serply API key
        Returns:
            str: The Serply API key
        """
        try:
            api_key = os.environ["SERPLY_API_KEY"]
        except Exception:
            raise Exception("Serply API key not found. Please set the SERPLY_API_KEY environment variable. "
                            "You can get a key at https://serply.io/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query using the Serply API
        Returns:
            list: List of search results with title, href, and body
        """
        print("Searching with query {0}...".format(self.query))

        # Build the query using Google search syntax for optional filters.
        query_with_filters = self.query
        if self.exclude_sites:
            for site in self.exclude_sites:
                query_with_filters += f" -site:{site}"
        if self.query_domains:
            query_with_filters += " site:" + " OR site:".join(self.query_domains)

        # Serply takes the query and result count as URL-encoded path segments.
        path = urllib.parse.urlencode({"q": query_with_filters, "num": max_results})
        url = f"https://api.serply.io/v1/search/{path}"
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            # Serply is fronted by Cloudflare, which rejects the default
            # requests User-Agent, so send an explicit one.
            "User-Agent": "gpt-researcher",
        }

        resp = requests.get(url, headers=headers, timeout=10)

        # Always return a list so callers (which do `len(...)` / iterate over
        # the result) never receive None.
        if resp is None:
            return []
        try:
            search_results = resp.json()
        except Exception:
            return []
        if not isinstance(search_results, dict):
            return []

        results = search_results.get("results") or []
        if not isinstance(results, list):
            return []

        search_results = []
        for result in results:
            if not isinstance(result, dict):
                continue
            href = result.get("link") or ""
            if not href:
                continue
            search_results.append(
                {
                    "title": result.get("title") or "",
                    "href": href,
                    "body": result.get("description") or "",
                }
            )

        return search_results
