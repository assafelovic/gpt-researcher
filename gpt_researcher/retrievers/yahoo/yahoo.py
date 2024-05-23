# Tavily API Retriever

# libraries
import os
from yahoo_search import search


class YahooSearch:
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

    def get_api_key(self):
        """
        Gets the Tavily API key
        Returns:

        """
        return "No API Key is required for this library"

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        try:
            # Search the query
            results = search(self.query)
            sources = results.pages
            if not sources:
                raise Exception("No results found with Tavily API search.")
            # Return the results
            search_response = [{"href": obj.link, "body": obj.text, "title": obj.title} for obj in sources]
        except Exception as e: # Fallback in case overload on Tavily Search API
            print(f"Error: {e}")
            search_response = []
        return search_response
