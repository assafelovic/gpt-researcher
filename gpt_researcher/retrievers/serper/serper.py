from __future__ import annotations

import json
import logging
import os

from typing import Any

import requests

logger: logging.Logger = logging.getLogger(__name__)


# class SerperSearch(BaseRetriever):
#    """Google Serper Search Retriever that implements LangChain's BaseRetriever interface."""

#    def __init__(
#        self,
#        headers: dict[str, str] | None = None,
#    ) -> None:
#        """Initialize the Serper retriever.

#        Args:
#            headers: Optional dictionary containing API keys. If not provided,
#                    will attempt to load from environment variables.
#        """
#        super().__init__()
#        self.headers: dict[str, str] = headers or {}
#        self.api_key: str = self.headers.get("serper_api_key") or self.get_api_key()

#    def get_api_key(self) -> str:
#        """Gets the Serper API key from environment variables.

#        Returns:
#            str: The Serper API key.

#        Raises:
#            Exception: If API key is not found in environment variables.
#        """
#        try:
#            api_key = os.environ["SERPER_API_KEY"]
#        except KeyError:
#            raise Exception("Serper API key not found. Please set the SERPER_API_KEY environment variable. You can get a key at https://serper.dev/")
#        return api_key

#    def _get_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 7,
#    ) -> list[Document]:
#        """Get documents relevant to a query using Serper Search API.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 7.

#        Returns:
#            List of relevant documents.
#        """
#        logger.info(f"Searching with query {query}...")

#        url = "https://google.serper.dev/search"
#        headers = {
#            "X-API-KEY": self.api_key,
#            "Content-Type": "application/json",
#        }
#        data = {
#            "q": query,
#            "num": max_results,
#        }

#        try:
#            response = requests.post(url, headers=headers, json=data, timeout=10)
#            response.raise_for_status()
#            search_results = response.json()
#        except Exception as e:
#            logger.exception(f"Failed fetching sources. Resulting in empty response. {e.__class__.__name__}: {e}")
#            return []

#        if not search_results or "organic" not in search_results:
#            return []

#        documents: list[Document] = []

#        # Convert search results to Document objects
#        for result in search_results["organic"]:
# Skip YouTube results
#            if "youtube.com" in result["link"]:
#                continue

# Create Document object with metadata
#            doc = Document(
#                page_content=result["snippet"],
#                metadata={
#                    "title": result["title"],
#                    "source": result["link"],
#                },
#            )
#            documents.append(doc)

#        return documents[:max_results]

#    async def _aget_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 7,
#    ) -> list[Document]:
#        """Asynchronously get documents relevant to a query using Serper Search API.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 7.

#        Returns:
#            List of relevant documents.
#        """
#        logger.info(f"Searching with query {query}...")

#        url = "https://google.serper.dev/search"
#        headers = {
#            "X-API-KEY": self.api_key,
#            "Content-Type": "application/json",
#        }
#        data = {
#            "q": query,
#            "num": max_results,
#        }

#        try:
#            async with httpx.AsyncClient() as client:
#                response = await client.post(url, headers=headers, json=data, timeout=10.0)
#                response.raise_for_status()
#                search_results = response.json()
#        except Exception as e:
#            logger.exception(f"Failed fetching sources. Resulting in empty response. {e.__class__.__name__}: {e}")
#            return []

#        if not search_results or "organic" not in search_results:
#            return []

#        documents: list[Document] = []

#        # Convert search results to Document objects
#        for result in search_results["organic"]:
# Skip YouTube results
#            if "youtube.com" in result["link"]:
#                continue

# Create Document object with metadata
#            doc = Document(
#                page_content=result["snippet"],
#                metadata={
#                    "title": result["title"],
#                    "source": result["link"],
#                    "body": result["snippet"],
#                },
#            )
#            documents.append(doc)

#        return documents[:max_results]
# =======


class SerperSearch:
    """Google Serper Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        *args: Any,  # provided for compatibility with other retrievers
        **kwargs: Any,  # provided for compatibility with other retrievers
    ) -> None:
        """Initializes the SerperSearch object.

        Args:
            query (str): The search query string.
            query_domains (list, optional): List of domains to include in the search. Defaults to None.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.query: str = query
        self.query_domains: list[str] | None = query_domains
        self.api_key: str = self.get_api_key()

    def get_api_key(self) -> str:
        """Gets the Serper API key.

        Returns:
            str: The Serper API key.

        Raises:
            Exception: If the Serper API key is not found in the environment variables.
        """
        try:
            api_key: str = os.environ["SERPER_API_KEY"]
        except KeyError:
            raise KeyError("Serper API key not found. Please set the SERPER_API_KEY environment variable. You can get a key at https://serper.dev/")
        return api_key

    def search(
        self,
        max_results: int = 7,
    ) -> list[dict[str, str]]:
        """Searches the query.

        Useful for general internet search queries using the Serp API.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing the search results.
        """
        print("Searching with query {0}...".format(self.query))

        # Search the query (see https://serper.dev/playground for the format)
        url: str = "https://google.serper.dev/search"

        headers: dict[str, str] = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        # TODO: Add support for query domains
        data: str = json.dumps(
            {
                "q": self.query,
                "num": max_results,
            }
        )

        resp: requests.Response = requests.request(
            "POST",
            url,
            timeout=10,
            headers=headers,
            data=data,
        )

        # Preprocess the results
        if resp is None:
            return []
        try:
            search_results: dict[str, Any] = json.loads(resp.text)
        except Exception:
            return []
        if search_results is None:
            return []

        results: list[dict[str, Any]] = search_results["organic"]
        search_results_list: list[dict[str, str]] = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in str(result["link"]).casefold():
                continue
            result_dict: dict[str, Any] = {
                "title": result["title"],
                "href": result["link"],
                "body": result["snippet"],
            }
            search_results_list.append(result_dict)

        return search_results_list
