# Tavily API Retriever

# libraries
import os
from tavily import TavilyClient
from gpt_researcher.config.config import Config


class TavilySearch():
    def __init__(self, query):
        self.query = query
        self.api_key = self.get_api_key()
        self.client = TavilyClient(self.api_key)


    def get_api_key(self):
        # Get the API key
        try:
            api_key = os.environ["TAVILY_API_KEY"]
        except:
            raise Exception("Tavily API key not found. Please set the TAVILY_API_KEY environment variable.")
        return api_key


    def search(self):
        # Search the query
        results = self.client.search(self.query, search_depth="advanced")
        # Return the results
        results = str(results["results"])
        return results