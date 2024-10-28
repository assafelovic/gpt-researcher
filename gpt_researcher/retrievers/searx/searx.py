import os
import json
import requests
from typing import List, Dict
from urllib.parse import urljoin


class SearxSearch():
    """
    SearxNG API Retriever
    """
    def __init__(self, query: str):
        """
        Initializes the SearxSearch object
        Args:
            query: Search query string
        """
        self.query = query
        self.base_url = self.get_searxng_url()

    def get_searxng_url(self) -> str:
        """
        Gets the SearxNG instance URL from environment variables
        Returns:
            str: Base URL of SearxNG instance
        """
        try:
            base_url = os.environ["SEARX_URL"]
            if not base_url.endswith('/'):
                base_url += '/'
            return base_url
        except KeyError:
            raise Exception(
                "SearxNG URL not found. Please set the SEARX_URL environment variable. "
                "You can find public instances at https://searx.space/"
            )

    def search(self, max_results: int = 7) -> List[Dict[str, str]]:
        """
        Searches the query using SearxNG API
        Args:
            max_results: Maximum number of results to return
        Returns:
            List of dictionaries containing search results
        """
        search_url = urljoin(self.base_url, "search")
        
        params = {
            'q': self.query,
            'format': 'json',
            'pageno': 1,
            'categories': 'general',
            'engines': 'google,bing,duckduckgo',  # TODO: Add environment variable to customize the engines
            'results': max_results
        }

        try:
            response = requests.get(
                search_url,
                params=params,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            results = response.json()

            # Normalize results to match the expected format
            search_response = []
            for result in results.get('results', [])[:max_results]:
                search_response.append({
                    "href": result.get('url', ''),
                    "body": result.get('content', '')
                })

            return search_response

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error querying SearxNG: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Error parsing SearxNG response")
