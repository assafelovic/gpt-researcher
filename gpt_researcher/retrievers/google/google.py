# Tavily API Retriever

# libraries
import os
import requests
import json


class GoogleSearch:
    """
    Google API Retriever
    """
    def __init__(self, query, headers=None, query_domains=None):
        """
        Initializes the GoogleSearch object
        Args:
            query:
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or None
        self.api_key = self.headers.get("google_api_key") or self.get_api_key()  # Use the passed api_key or fallback to environment variable
        self.cx_key = self.headers.get("google_cx_key") or self.get_cx_key()  # Use the passed cx_key or fallback to environment variable

    def get_api_key(self):
        """
        Gets the Google API key
        Returns:

        """
        # Get the API key
        try:
            api_key = os.environ["GOOGLE_API_KEY"]
        except:
            raise Exception("Google API key not found. Please set the GOOGLE_API_KEY environment variable. "
                            "You can get a key at https://developers.google.com/custom-search/v1/overview")
        return api_key

    def get_cx_key(self):
        """
        Gets the Google CX key
        Returns:

        """
        # Get the API key
        try:
            api_key = os.environ["GOOGLE_CX_KEY"]
        except:
            raise Exception("Google CX key not found. Please set the GOOGLE_CX_KEY environment variable. "
                            "You can get a key at https://developers.google.com/custom-search/v1/overview")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query using Google Custom Search API, optionally restricting to specific domains
        Returns:
            list: List of search results with title, href and body
        """
        # Build query with domain restrictions if specified
        search_query = self.query
        if self.query_domains and len(self.query_domains) > 0:
            domain_query = " OR ".join([f"site:{domain}" for domain in self.query_domains])
            search_query = f"({domain_query}) {self.query}"

        print("Searching with query {0}...".format(search_query))

        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx_key}&q={search_query}&start=1"
        resp = requests.get(url)

        if resp.status_code < 200 or resp.status_code >= 300:
            print("Google search: unexpected response status: ", resp.status_code)

        if resp is None:
            return
        try:
            search_results = json.loads(resp.text)
        except Exception:
            return
        if search_results is None:
            return

        results = search_results.get("items", [])
        search_results = []

        # Normalizing results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in result["link"]:
                continue
            try:
                search_result = {
                    "title": result["title"],
                    "href": result["link"],
                    "body": result["snippet"],
                }
            except:
                continue
            search_results.append(search_result)

        return search_results[:max_results]
