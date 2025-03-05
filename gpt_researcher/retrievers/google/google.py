# Tavily API Retriever
from __future__ import annotations

import json
import os

from typing import TYPE_CHECKING, Any

import requests

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

logger: logging.Logger = get_formatted_logger(__name__)


# class GoogleSearch(BaseRetriever):
#    """Google API Retriever that implements LangChain's BaseRetriever interface."""

#    def __init__(
#        self,
#        headers: dict[str, str] | None = None,
#    ) -> None:
#        """Initialize the GoogleSearch retriever.

#        Args:
#            headers: Optional dictionary containing API keys. If not provided,
#                    will attempt to load from environment variables.
#        """
#        super().__init__()

#    def _get_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 7,
#    ) -> list[Document]:
#        """Get documents relevant to a query using google Custom Search API.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 7.

#        Returns:
#            List of relevant documents.
#        """
#        logger.info(f"Searching with query {query}...")
#        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx_key}&q={query}&start=1"
#        resp = requests.get(url)

#        if resp.status_code < 200 or resp.status_code >= 300:
#            logger.warning("Google search: unexpected response status: ", resp.status_code)
#            return []

#        try:
#            search_results = json.loads(resp.text)
#        except Exception:
#            return []

#        if search_results is None:
#            return []

#        results: list[dict[str, str]] = search_results.get("items", [])
#        documents: list[Document] = []

# Convert search results to Document objects
#        for result in results:
#            # Skip YouTube results
#            if "youtube.com" in result["link"]:
#                continue

#            try:
#                # Create Document object with metadata
#                doc = Document(
#                    page_content=result["snippet"],
#                    metadata={
#                        "title": result["title"],
#                        "source": result["link"],
#                    },
#                )
#                documents.append(doc)
#            except KeyError:
#                continue

#        return documents[:max_results]

#    async def _aget_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 7,
#    ) -> list[Document]:
#        """Asynchronously get documents relevant to a query.

#        This implementation uses async HTTP calls for better performance.
#        """
#        logger.info(f"Searching with query {query}...")
#        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx_key}&q={query}&start=1"

#        async with httpx.AsyncClient() as client:
#            resp = await client.get(url)

#        if resp.status_code < 200 or resp.status_code >= 300:
#            logger.warning("Google search: unexpected response status: ", resp.status_code)
#            return []

#        try:
#            search_results = resp.json()
#        except Exception:
#            return []

#        if search_results is None:
#            return []

#        results = search_results.get("items", [])
#        documents: list[Document] = []

# Convert search results to Document objects
#        for result in results:
# Skip YouTube results
#            if "youtube.com" in result["link"]:
#                continue

#            try:
#                # Create Document object with metadata
#                doc = Document(
#                    page_content=result["snippet"],
#                    metadata={
#                        "title": result["title"],
#                        "source": result["link"],
#                    },
#                )
#                documents.append(doc)
#            except KeyError:
#                continue

#        return documents[:max_results]


class GoogleSearch:
    """Google API Retriever."""

    def __init__(
        self,
        query: str,
        headers: dict[str, str] | None = None,
        query_domains: list[str] | None = None,
        *args: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ) -> None:
        """Initializes the GoogleSearch object.

        Args:
            query: The search query
            headers: The headers to use for the request
            query_domains: The domains to filter the search by
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.query: str = query
        self.headers: dict[str, str] = headers or {}
        self.api_key: str = self.headers.get("google_api_key") or self.get_api_key()
        self.cx_key: str = self.headers.get("google_cx_key") or self.get_cx_key()
        self.query_domains: list[str] | None = query_domains or None
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

    def get_api_key(self) -> str:
        """Gets the Google API key from environment variables.

        Returns:
            str: The Google API key.

        Raises:
            Exception: If API key is not found in environment variables.
        """
        try:
            api_key: str = os.environ["GOOGLE_API_KEY"]
        except KeyError:
            raise Exception(
                "Google API key not found. Please set the GOOGLE_API_KEY environment variable. You can get a key at https://developers.google.com/custom-search/v1/overview"
            )
        else:
            return api_key

    def get_cx_key(self) -> str:
        """Gets the Google CX key from environment variables.

        Returns:
            str: The Google CX key.

        Raises:
            Exception: If CX key is not found in environment variables.
        """
        try:
            api_key: str = os.environ["GOOGLE_CX_KEY"]
        except KeyError:
            raise Exception(
                "Google CX key not found. Please set the GOOGLE_CX_KEY environment variable. You can get a key at https://developers.google.com/custom-search/v1/overview"
            )
        else:
            return api_key

    def search(
        self,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """Searches the query.

        Useful for general internet search queries using Google.

        Returns:
            list: List of search results with title, href and body
        """
        # If max_results is the default, check environment variable
        if max_results is None:  # Default value
            max_results = int(os.environ.get("MAX_SOURCES", 10))

        logger.info(f"GoogleSearch: Searching with query:{os.linesep*2}```{self.query}{os.linesep}```")

        # Build query with domain restrictions if specified
        search_query: str = self.query
        if self.query_domains and len(self.query_domains) > 0:
            domain_query: str = " OR ".join([f"site:{domain}" for domain in self.query_domains])
            search_query: str = f"({domain_query}) {self.query}"

        logger.info(f"Searching with query {search_query}...")

        url: str = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx_key}&q={search_query}&start=1"
        resp: requests.Response = requests.get(url)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning(f"Google search: unexpected response status: {resp.status_code}")

        if resp is None:
            return []
        try:
            search_results: dict[str, Any] = json.loads(resp.text)
        except Exception as e:
            logger.warning("Google search: unexpected response text: ", resp.text)
            logger.exception(f"{e.__class__.__name__}: {e}")
            return []
        else:
            if search_results is None:
                logger.debug("Google search: no results found")
                return []

        results: list[dict[str, str]] | None = search_results.get("items")
        if not results:
            logger.debug("Google search: no results found")
            return []

        # Normalizing results to match the format of the other search APIs
        search_results_list: list[dict[str, str]] = []
        for result in results:
            # skip youtube results
            if "youtube.com" in str(result["link"]).casefold():
                logger.debug("Google search: skipping youtube result")
                continue
            try:
                search_result: dict[str, str] = {
                    "title": result["title"],
                    "href": result["link"],
                    "body": result["snippet"],
                }
            except Exception as e:
                logger.warning("Google search: unexpected result: ", result)
                logger.exception(f"{e.__class__.__name__}: {e}")
                continue
            else:
                search_results_list.append(search_result)

        return search_results_list[:max_results]
