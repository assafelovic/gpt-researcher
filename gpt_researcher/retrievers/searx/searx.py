import os
import json
import requests
from typing import List, Dict
from urllib.parse import urljoin

# gpt_researcher.skills.researcher._search_relevant_source_urls() treats
# any search result whose raw_content/body exceeds 100 characters as
# already-fetched full text -- a heuristic meant for retrievers (e.g.
# PubMed Central) that genuinely return full article text inline. SearxNG
# populates "body" with an ordinary search-result snippet, which routinely
# exceeds 100 characters, so without this cap every result is wrongly
# treated as already-fetched and the real page is never actually scraped
# (get_source_urls() then returns [] and reports ship with zero verifiable
# citations). Capped here, at the source, rather than patched in
# _search_relevant_source_urls() itself, so any future upstream change to
# that function's classification logic (bug fixes, new bookkeeping) is
# inherited automatically. The truncated snippet is only ever used for
# that classification decision and early-stage sub-query planning -- once
# a URL takes the real scrape path, gpt-researcher fetches and uses the
# actual page content, not this snippet.
_MAX_PREFETCHED_LEN = 100


class SearxSearch():
    """
    SearxNG API Retriever
    """
    def __init__(self, query: str, query_domains=None):
        """
        Initializes the SearxSearch object
        Args:
            query: Search query string
        """
        self.query = query
        self.query_domains = query_domains or None
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

    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Searches the query using SearxNG API
        Args:
            max_results: Maximum number of results to return
        Returns:
            List of dictionaries containing search results
        """
        search_url = urljoin(self.base_url, "search")
        # TODO: Add support for query domains
        params = {
            # The search query.
            'q': self.query,
            # Output format of results. Format needs to be activated in searxng config.
            'format': 'json'
        }

        try:
            response = requests.get(
                search_url,
                params=params,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            results = response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error querying SearxNG: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Error parsing SearxNG response")

        if not isinstance(results, dict):
            return []

        search_response = []
        raw_results = results.get('results', [])
        if not isinstance(raw_results, list):
            return []

        for result in raw_results:
            if not isinstance(result, dict):
                continue
            href = result.get('url') or result.get('href') or ''
            if not href:
                continue
            body = result.get('content') or result.get('snippet') or ''
            search_response.append({
                "href": href,
                "body": body[:_MAX_PREFETCHED_LEN],
            })
            if len(search_response) >= max_results:
                break

        return search_response
