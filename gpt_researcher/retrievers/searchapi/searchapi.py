# SearchApi Retriever

# libraries
import os
import requests
import urllib.parse


class SearchApiSearch():
    """
    SearchApi Retriever
    """
    def __init__(self, query, query_domains=None):
        """
        Initializes the SearchApiSearch object
        Args:
            query:
        """
        self.query = query
        self.api_key = self.get_api_key()

    def get_api_key(self):
        """
        Gets the SearchApi API key
        Returns:

        """
        try:
            api_key = os.environ["SEARCHAPI_API_KEY"]
        except:
            raise Exception("SearchApi key not found. Please set the SEARCHAPI_API_KEY environment variable. "
                            "You can get a key at https://www.searchapi.io/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        print("SearchApiSearch: Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using SearchApi."""


        url = "https://www.searchapi.io/api/v1/search"
        params = {
            "q": self.query,
            "engine": "google",
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-SearchApi-Source': 'gpt-researcher'
        }

        encoded_url = url + "?" + urllib.parse.urlencode(params)
        search_response = []

        try:
            response = requests.get(encoded_url, headers=headers, timeout=20)
            if response.status_code == 200:
                search_results = response.json()
                if search_results:
                    results = search_results["organic_results"]
                    results_processed = 0
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
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []

        return search_response
