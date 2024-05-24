# Tavily API Retriever

# libraries
import os
from tavily import TavilyClient
from duckduckgo_search import DDGS
from yahoo_search import search


class TavilySearch():
    """
    Tavily API Retriever
    """
    def __init__(self, query, topic="general"):
        """
        Initializes the TavilySearch object
        Args:
            query:
        """
        self.query = query
        self.api_key = self.get_api_key()
        self.client = TavilyClient(self.api_key)
        self.topic = topic

    def get_api_key(self):
        """
        Gets the Tavily API key
        Returns:

        """
        # Get the API key
        try:
            api_key = os.environ["TAVILY_API_KEY"]
        except:
            raise Exception("Tavily API key not found. Please set the TAVILY_API_KEY environment variable. "
                            "You can get a key at https://app.tavily.com")
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
                print(f"Error: {e}. Fallback to Yahoo Search API...")
                search_response = [{"href": obj.link, "body": obj.text, "title": obj.title} for obj in search(self.query).pages]
        return search_response
