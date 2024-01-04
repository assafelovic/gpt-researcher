# Bing Search Retriever

# libraries
import os
import requests
import json


class BingSearch():
    """
    Bing Search Retriever
    """
    def __init__(self, query):
        """
        Initializes the BingSearch object
        Args:
            query:
        """
        self.query = query
        self.api_key = self.get_api_key()

    def get_api_key(self):
        """
        Gets the Bing API key
        Returns:

        """
        try:
            api_key = os.environ["BING_API_KEY"]
        except:
            raise Exception("Bing API key not found. Please set the BING_API_KEY environment variable.")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using the Bing API."""


        # Search the query
        url = "https://api.bing.microsoft.com/v7.0/search"

        headers = {
        'Ocp-Apim-Subscription-Key': self.api_key,
        'Content-Type': 'application/json'
        }
        params = {
            "responseFilter" : "Webpages",
            "q": self.query,
            "count": max_results,
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
            "safeSearch": "Strict"
        }
        
        resp = requests.get(url, headers=headers, params=params)

        # Preprocess the results
        if resp is None:
            return
        try:
            search_results = json.loads(resp.text)
        except Exception:
            return
        if search_results is None:
            return

        results = search_results["webPages"]["value"]
        search_results = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in result["url"]:
                continue
            search_result = {
                "title": result["name"],
                "href": result["url"],
                "body": result["snippet"],
            }
            search_results.append(search_result)

        return search_results
