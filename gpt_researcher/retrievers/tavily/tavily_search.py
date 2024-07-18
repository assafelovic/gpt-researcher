# Tavily API Retriever

# libraries
import os
from tavily import TavilyClient
from duckduckgo_search import DDGS


class TavilySearch():
    """
    Tavily API Retriever
    """
    def __init__(self, query, headers=None, topic="general"):
        """
        Initializes the TavilySearch object
        Args:
            query:
        """
        self.query = query
        self.headers = headers or {}
        self.api_key = self.get_api_key()
        self.client = TavilyClient(self.api_key)
        self.topic = topic

    def get_api_key(self):
        """
        Gets the Tavily API key
        Returns:

        """
        api_key = self.headers.get("tavily_api_key")
        if not api_key:
            try:
                api_key = os.environ["TAVILY_API_KEY"]
            except KeyError:
                raise Exception("Tavily API key not found. Please set the TAVILY_API_KEY environment variable.")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        try:
            # Search the query
            results = self.client.search(self.query, search_depth="basic", max_results=max_results, topic=self.topic)
            sources = results.get("results", [])
            if not sources:
                raise Exception("No results found with Tavily API search.")
            # Return the results
            search_response = [{"href": obj["url"], "body": obj["content"]} for obj in sources]
        except Exception as e: # Fallback in case overload on Tavily Search API
            print(f"Error: {e}. Fallback to DuckDuckGo Search API...")
            try:
                ddg = DDGS()
                search_response = ddg.text(self.query, region='wt-wt', max_results=max_results)
            except Exception as e:
                print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
                search_response = []
        return search_response
