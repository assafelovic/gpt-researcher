"""Tavily API search retriever for GPT Researcher.

This module provides the TavilySearch class for performing web searches
using the Tavily API.
"""

import json
import os
import re
from typing import Literal, Optional, Sequence

import requests

# Google-style site:domain operators, which the Tavily API does not support.
_SITE_OPERATOR_PATTERN = re.compile(r"site:(\S+)", re.IGNORECASE)


class TavilySearch:
    """
    Tavily API Retriever
    """

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        """
        Initializes the TavilySearch object.

        Args:
            query (str): The search query string.
            headers (dict, optional): Additional headers to include in the request. Defaults to None.
            topic (str, optional): The topic for the search. Defaults to "general".
            query_domains (list, optional): List of domains to include in the search. Defaults to None.
        """
        self.query = query
        self.headers = headers or {}
        self.topic = topic
        self.base_url = "https://api.tavily.com/search"
        self.api_key = self.get_api_key()
        self.headers = {
            "Content-Type": "application/json",
        }
        self.query_domains = query_domains or None

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
                print(
                    "Tavily API key not found, set to blank. If you need a retriver, please set the TAVILY_API_KEY environment variable."
                )
                return ""
        return api_key


    def _search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = "basic",
        topic: str = "general",
        days: int = 2,
        max_results: int = 10,
        include_domains: Sequence[str] = None,
        exclude_domains: Sequence[str] = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        use_cache: bool = True,
    ) -> dict:
        """
        Internal search method to send the request to the API.
        """

        data = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "days": days,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "max_results": max_results,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_images": include_images,
            "api_key": self.api_key,
            "use_cache": use_cache,
        }

        response = requests.post(
            self.base_url, data=json.dumps(data), headers=self.headers, timeout=100
        )

        if response.status_code == 200:
            return response.json()
        else:
            # Raises a HTTPError if the HTTP request returned an unsuccessful status code
            response.raise_for_status()

    def search(self, max_results=10):
        """
        Searches the query
        Returns:

        """
        try:
            # LLM-generated queries often use Google-style site: operators,
            # which Tavily rejects (returning zero results). Translate them
            # into Tavily's include_domains parameter instead.
            query = self.query
            include_domains = self.query_domains
            site_domains = _SITE_OPERATOR_PATTERN.findall(query)
            if site_domains:
                query = _SITE_OPERATOR_PATTERN.sub("", query).strip()
                # Keep only the domain part (Tavily matches domains, not paths)
                site_domains = [d.strip(",").split("/")[0] for d in site_domains]
                include_domains = list(dict.fromkeys(site_domains + (include_domains or [])))

            # Search the query (Tavily rejects queries longer than 400 chars)
            results = self._search(
                query[:400],
                search_depth="basic",
                max_results=max_results,
                topic=self.topic,
                include_domains=include_domains,
            )
            sources = results.get("results", [])
            if not sources:
                raise Exception("No results found with Tavily API search.")
            # Return the results; skip non-dict / missing-URL items so one bad
            # payload entry does not KeyError the whole search() call.
            search_response = []
            for obj in sources:
                if not isinstance(obj, dict):
                    continue
                url = obj.get("url") or obj.get("href")
                if not url:
                    continue
                body = obj.get("content") or obj.get("snippet") or obj.get("body") or ""
                search_response.append({"href": url, "body": body})
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response
