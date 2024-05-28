# Tavily API Retriever

# libraries
import os
from tavily import TavilyClient
from langchain_community.utilities import SearxSearchWrapper


class SearxSearch():
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
            api_key = os.environ["SEARX_URL"]
        except:
            raise Exception("Searx URL key not found. Please set the SEARX_URL environment variable. "
                            "You can get your key from https://searx.space/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        searx = SearxSearchWrapper(searx_host=os.environ["SEARX_URL"])
        results = searx.results(self.query, max_results)
        # Normalizing results to match the format of the other search APIs
        search_response = [{"href": obj["link"], "body": obj["snippet"]} for obj in results]
        return search_response
