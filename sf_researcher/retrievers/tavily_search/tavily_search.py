# tavily_search.py

# libraries
import os
from ..tavily_api import TavilyClient
from duckduckgo_search import DDGS


class TavilySearch():
    """
    Tavily API Retriever
    """
    def __init__(
        self, 
        query, 
        include_domains: list = [],
        exclude_domains: list = []
    ):
        """
        Initializes the TavilySearch object
        Args:
            query:
            include_domains (list): List of domains to include in the search (optional)
            exclude_domains (list): List of domains to exclude from the search (optional)
        """
        self.query = query
        self.api_key = self.get_api_key()
        self.client = TavilyClient(api_key=self.api_key, include_domains=include_domains, exclude_domains=exclude_domains)

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
        # try:
        #     # Search the query
        #     results = self.client.search(self.query, search_depth="basic", max_results=max_results)
        #     sources = results.get("results", [])
        #     if not sources:
        #         raise Exception("No results found with Tavily API search.")
        #     # Return the results
        #     search_response = [
        #         {
        #             "url": obj["url"],
        #             "title": obj.get("title", ""),
        #             "score": obj.get("score", 0.0),
        #             "raw_content": obj.get("raw_content", ""),
        #         }
        #         for obj in sources
        #     ]
        # except Exception as e: # Fallback in case overload on Tavily Search API
        #     print(f"Error: {e}. Fallback to DuckDuckGo Search API...")
        #     ddg = DDGS()
        #     search_response = ddg.text(self.query, region='wt-wt', max_results=max_results)
        # return search_response

        try:
            # Search the query
            results = self.client.search(self.query, search_depth="basic", max_results=max_results)
            sources = results.get("results", [])
            if not sources:
                raise Exception("No results found with Tavily API search.")
            # Return the results
            search_response = [{"href": obj["url"], "body": obj["content"]} for obj in sources]
        except Exception as e: # Fallback in case overload on Tavily Search API
            print(f"Error: {e}. Fallback to DuckDuckGo Search API...")
            ddg = DDGS()
            search_response = ddg.text(self.query, region='wt-wt', max_results=max_results)
        return search_response