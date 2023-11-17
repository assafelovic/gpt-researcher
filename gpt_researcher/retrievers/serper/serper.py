# Tavily API Retriever

# libraries
import os
import requests
import json
from tavily import TavilyClient


class SerpSearch():
    """
    Tavily API Retriever
    """
    def __init__(self, query):
        """
        Initializes the TavilySearch object
        Args:
            query:
        """
        self.query = query
        self.api_key = self.get_api_key()
        self.client = TavilyClient(self.api_key)

    def get_api_key(self):
        """
        Gets the Tavily API key
        Returns:

        """
        # Get the API key
        try:
            api_key = os.environ["SERP_API_KEY"]
        except:
            raise Exception("Serp API key not found. Please set the SERP_API_KEY environment variable. "
                            "You can get a key at https://serper.dev/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using the Serp API."""
        url = "https://serpapi.com/search.json?engine=google&q=" + self.query + "&api_key=" + self.api_key
        resp = requests.request("GET", url)

        if resp is None:
            return
        try:
            search_results = json.loads(resp.text)
        except Exception:
            return
        if search_results is None:
            return

        results = search_results["organic_results"]
        search_results = []

        # Normalizing results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in result["link"]:
                continue
            search_result = {
                "title": result["title"],
                "href": result["link"],
                "body": result["snippet"],
            }
            search_results.append(search_result)

        return search_results
