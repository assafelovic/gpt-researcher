"""You.com Search API retriever for GPT Researcher.

This module provides the YouSearch class for performing web searches
using the You.com Search API (https://documentation.you.com/quickstart).
"""

import logging
import os
from typing import Optional

import requests


BASE_URL = "https://ydc-index.io/v1/search"
DEFAULT_TIMEOUT = 10

logger = logging.getLogger(__name__)


class YouSearch:
    """
    You.com Search API Retriever with optional locale support.

    Locale parameters follow the You.com Search API spec:

    * ``country`` is an ISO-3166 alpha-2 code, e.g. ``US``, ``GB``, ``SA``
      (Saudi Arabia), ``JP`` (Japan).
    * ``language`` is a BCP-47 language tag, e.g. ``en``, ``ar`` (Arabic),
      ``ja`` (Japanese). The user-facing kwarg is ``language`` for
      readability but the wire parameter is ``search_lang``.

    Both kwargs fall back to the ``YOU_COUNTRY`` and ``YOU_SAFE_SEARCH``
    environment variables, mirroring Serper's ``SERPER_REGION`` /
    ``SERPER_LANGUAGE`` precedent.
    """

    def __init__(
        self,
        query,
        headers=None,
        topic="general",
        query_domains=None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """
        Initializes the YouSearch object.

        Args:
            query (str): The search query string.
            headers (dict, optional): Additional headers to include in the request.
                May contain ``you_api_key`` for per-request key override. Defaults to None.
            topic (str, optional): The topic for the search. Defaults to "general".
            query_domains (list, optional): List of domains to include in the search.
                Defaults to None.
            country (str, optional): ISO-3166 alpha-2 country code (e.g. ``SA``,
                ``JP``). Falls back to the ``YOU_COUNTRY`` env var.
            language (str, optional): BCP-47 language tag (e.g. ``ar``, ``ja``).
                Sent on the wire as ``search_lang``. Falls back to the
                ``YOU_SAFE_SEARCH`` env var.
        """
        self.query = query
        self.headers = headers or {}
        self.topic = topic
        self.query_domains = query_domains or None
        self.country = country or os.getenv("YOU_COUNTRY")
        self.language = language or os.getenv("YOU_SAFE_SEARCH")

    def _get_api_key(self):
        """
        Resolves the You.com API key. The ``you_api_key`` header takes
        precedence over the ``YOU_API_KEY`` environment variable so that
        callers (e.g. the backend server) may inject per-request keys.
        """
        api_key = self.headers.get("you_api_key")
        if not api_key:
            api_key = os.environ.get("YOU_API_KEY", "")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query against the You.com Search API.

        Args:
            max_results (int): Maximum number of results to return. Defaults to 7.

        Returns:
            list[dict]: A list of result dicts with keys ``href``, ``body``, ``title``.
        """
        api_key = self._get_api_key()
        if not api_key:
            logger.warning(
                "You.com API key not found, set to blank. If you need a retriver, "
                "please set the YOU_API_KEY environment variable."
            )
            return []

        params = {
            "query": self.query,
            "count": max_results,
        }
        if self.country:
            params["country"] = self.country
        if self.language:
            params["search_lang"] = self.language

        try:
            response = requests.get(
                BASE_URL,
                headers={"X-API-Key": api_key},
                params=params,
                timeout=DEFAULT_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            logger.warning(
                "You.com Search request timed out after %ss. Returning empty results.",
                DEFAULT_TIMEOUT,
            )
            return []
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "You.com Search request failed: %s. Returning empty results.", exc
            )
            return []

        if response.status_code != 200:
            logger.warning(
                "You.com Search returned HTTP %s. Returning empty results.",
                response.status_code,
            )
            return []

        payload = response.json()
        web_results = payload.get("results", {}).get("web", [])

        search_response = []
        for item in web_results:
            snippets = item.get("snippets") or []
            body = " ".join(snippets) if snippets else item.get("description", "")
            search_response.append(
                {
                    "href": item.get("url", ""),
                    "body": body,
                    "title": item.get("title", ""),
                }
            )

        return search_response
