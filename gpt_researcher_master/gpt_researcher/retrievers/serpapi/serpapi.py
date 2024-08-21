# SerpApi Retriever

# libraries
import os
import requests
from duckduckgo_search import DDGS
import urllib.parse


class SerpApiSearch():
    """
    SerpApi Retriever
    """
    def __init__(self, query):
        """
        Initializes the SerpApiSearch object
        Args:
            query:
        """
        self.query = query
        self.api_key = self.get_api_key()

    def get_api_key(self):
        """
        Gets the SerpApi API key
        Returns:

        """
        try:
            api_key = os.environ["SERPAPI_API_KEY"]
        except:
            raise Exception("SerpApi API key not found. Please set the SERPAPI_API_KEY environment variable. "
                            "You can get a key at https://serpapi.com/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        print("SerpApiSearch: Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using SerpApi."""


        url = "https://serpapi.com/search.json"
        params = {
            "q": self.query,
            "api_key": self.api_key
        }
        encoded_url = url + "?" + urllib.parse.urlencode(params)
        search_response = []
        try:
            response = requests.get(encoded_url, timeout=10)
            if response.status_code == 200:
                search_results = response.json()
                if search_results:
                    results = search_results["organic_results"]
                    for result in results:
                        # skip youtube results
                        if "youtube.com" in result["link"]:
                            continue
                        if results_processed >= max_results:
                            break
                        search_result = {
                            "title": result["title"],
                            "href": result["link"],
                            "body": result["snippet"],
                        }
                        search_response.append(search_result)
                        results_processed += 1    
        except Exception as e: # Fallback in case overload on Tavily Search API
            print(f"Error: {e}")
            ddg = DDGS()
            search_response = ddg.text(self.query, region='wt-wt', max_results=max_results)

        return search_response
