# SerpApi Retriever

# libraries
import os
import requests
import urllib.parse


class SerpApiSearch():
    """
    SerpApi Retriever
    """
    def __init__(self, query, query_domains=None):
        """
        Initializes the SerpApiSearch object
        Args:
            query:
        """
        self.query = query
        self.query_domains = query_domains or None
        self.api_key = self.get_api_key()

    def get_api_key(self):
        """
        Gets the SerpApi API key
        Returns:

        """
        try:
            api_key = os.environ["SERPAPI_API_KEY"]
        except Exception:
            raise Exception("SerpApi API key not found. Please set the SERPAPI_API_KEY environment variable. "
                            "You can get a key at https://serpapi.com/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        """Useful for general internet search queries using SerpApi."""
        if max_results <= 0:
            return []

        search_query = self.query
        if self.query_domains and len(self.query_domains) > 0:
            clean_domains = [
                d.strip()
                for d in self.query_domains
                if isinstance(d, str) and d.strip()
            ]
            if clean_domains:
                domain_query = " OR ".join(
                    [f"site:{domain}" for domain in clean_domains]
                )
                search_query = f"({domain_query}) {self.query}"

        print(f"SerpApiSearch: Searching with query {search_query}...")

        url = "https://serpapi.com/search.json"

        params = {"q": search_query, "api_key": self.api_key}
        encoded_url = url + "?" + urllib.parse.urlencode(params)
        search_response = []
        try:
            response = requests.get(encoded_url, timeout=10)
            if response.status_code == 200:
                search_results = response.json()
                if search_results:
                    # A response with no organic results (e.g. an error payload
                    # or a query that matched nothing) has no "organic_results"
                    # key; default to [] instead of raising KeyError.
                    results = search_results.get("organic_results") or []
                    if not isinstance(results, list):
                        results = []
                    results_processed = 0
                    for result in results:
                        if results_processed >= max_results:
                            break
                        if not isinstance(result, dict):
                            continue
                        link = result.get("link") or ""
                        # A result without a link is unusable; skip it rather
                        # than emitting an entry with href=None.
                        if not link:
                            continue
                        # skip youtube results
                        if "youtube.com" in link:
                            continue
                        search_result = {
                            "title": result.get("title") or "",
                            "href": link,
                            "body": result.get("snippet") or "",
                        }
                        search_response.append(search_result)
                        results_processed += 1
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []

        return search_response
