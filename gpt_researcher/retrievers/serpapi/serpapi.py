# SerpApi Retriever

# libraries
import os
import requests
import json


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
        raise NotImplementedError("SerpApiSearch is not fully implemented yet.")
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
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using SerpApi."""


        # Perform the search
        # TODO: query needs to be url encoded, so the code won't work as is.
        # Encoding should look something like this (but this is untested):
        # url_encoded_query = self.query.replace(" ", "+")
        url = "https://serpapi.com/search.json?engine=google&q=" + self.query + "&api_key=" + self.api_key
        resp = requests.request("GET", url)

        # Preprocess the results
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
