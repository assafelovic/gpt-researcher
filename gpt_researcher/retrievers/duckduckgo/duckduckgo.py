"""DuckDuckGo web search retriever.

This implementation uses DuckDuckGo's HTML endpoint directly so it works
without the external `ddgs` package.
"""

from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class Duckduckgo:
    """
    Duckduckgo API Retriever
    """
    def __init__(self, query, query_domains=None):
        self.query = query
        self.query_domains = query_domains or None

    def search(self, max_results=5):
        """
        Performs the search
        :param query:
        :param max_results:
        :return:
        """
        # TODO: Add support for query domains
        try:
            search_response = self._search(max_results=max_results)
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response

    def _search(self, max_results: int = 5) -> list[dict[str, str]]:
        params = {
            "q": self.query,
            "kl": "wt-wt",
            "kp": "-2",
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            )
        }

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params=params,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []
        for result in soup.select(".result")[:max_results]:
            title_link = result.select_one(".result__title a")
            snippet = result.select_one(".result__snippet")
            if not title_link:
                continue

            href = title_link.get("href", "").strip()
            if href.startswith("//"):
                href = f"https:{href}"
            elif href.startswith("/"):
                href = urljoin("https://duckduckgo.com", href)

            title = title_link.get_text(" ", strip=True)
            body = snippet.get_text(" ", strip=True) if snippet else ""

            results.append(
                {
                    "title": title,
                    "href": href,
                    "body": body,
                    "url": href,
                    "content": body,
                }
            )

        return results
