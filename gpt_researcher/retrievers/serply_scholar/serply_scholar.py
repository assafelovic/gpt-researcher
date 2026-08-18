# Serply Scholar Retriever

# libraries
import os
import urllib.parse
import requests


class SerplyScholarSearch():
    """
    Serply Scholar Retriever (Google Scholar results via the Serply SERP API)
    """
    def __init__(self, query, query_domains=None):
        """
        Initializes the SerplyScholarSearch object
        Args:
            query (str): The search query string.
            query_domains (list, optional): Unused; kept for a uniform retriever interface.
        """
        self.query = query
        self.api_key = self.get_api_key()

    def get_api_key(self):
        """
        Gets the Serply API key
        Returns:
            str: The Serply API key
        """
        try:
            api_key = os.environ["SERPLY_API_KEY"]
        except Exception:
            raise Exception("Serply API key not found. Please set the SERPLY_API_KEY environment variable. "
                            "You can get a key at https://serply.io/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query against Google Scholar using the Serply API
        Returns:
            list: List of scholarly results with title, href, and body
        """
        print("Searching scholar with query {0}...".format(self.query))

        # Serply takes the query and result count as URL-encoded path segments.
        path = urllib.parse.urlencode({"q": self.query, "num": max_results})
        url = f"https://api.serply.io/v1/scholar/{path}"
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            # Serply is fronted by Cloudflare, which rejects the default
            # requests User-Agent, so send an explicit one.
            "User-Agent": "gpt-researcher",
        }

        resp = requests.get(url, headers=headers, timeout=10)

        # Always return a list so callers (which do `len(...)` / iterate over
        # the result) never receive None.
        if resp is None:
            return []
        try:
            search_results = resp.json()
        except Exception:
            return []
        if not isinstance(search_results, dict):
            return []

        articles = search_results.get("articles") or []
        if not isinstance(articles, list):
            return []

        results = []
        for article in articles:
            if not isinstance(article, dict):
                continue
            href = article.get("link") or ""
            if not href:
                continue
            author = article.get("author") or {}
            names = author.get("names") if isinstance(author, dict) else None
            body = article.get("description") or ""
            if names:
                body = f"{names}. {body}" if body else names
            results.append(
                {
                    "title": article.get("title") or "",
                    "href": href,
                    "body": body,
                }
            )

        return results
