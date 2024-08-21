# Google Serper Retriever

# libraries
import os
import requests
import json


class SerperSearch():
    """
    Google Serper Retriever
    """
    def __init__(self, query):
        """
        Initializes the SerperSearch object
        Args:
            query:
        """
        self.query = query
        self.api_key = self.get_api_key()

    def get_api_key(self):
        """
        Gets the Serper API key
        Returns:

        """
        try:
            api_key = os.environ["SERPER_API_KEY"]
        except:
            raise Exception("Serper API key not found. Please set the SERPER_API_KEY environment variable. "
                            "You can get a key at https://serper.dev/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using the Serp API."""


        # Search the query (see https://serper.dev/playground for the format)
        url = "https://google.serper.dev/search"

        headers = {
        'X-API-KEY': self.api_key,
        'Content-Type': 'application/json'
        }
        data = json.dumps({"q": self.query, "num": max_results})

        resp = requests.request("POST", url, timeout=10, headers=headers, data=data)

        # Preprocess the results
        if resp is None:
            return
        try:
            search_results = json.loads(resp.text)
        except Exception:
            return
        if search_results is None:
            return

        results = search_results["organic"]
        search_results = []

        # Normalize the results to match the format of the other search APIs
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
