from __future__ import annotations

import logging
import os

from typing import Any, ClassVar, Dict, cast

# import httpx
from aiohttp_retry import Optional
import requests

# from langchain_core.callbacks import CallbackManagerForRetrieverRun
# from langchain_core.documents import Document
# from langchain_core.retrievers import BaseRetriever

logger: logging.Logger = logging.getLogger(__name__)


# class SemanticScholarSearch(BaseRetriever):
#     """Semantic Scholar Search Retriever that implements LangChain's BaseRetriever interface."""

#    BASE_URL: ClassVar[str] = "https://api.semanticscholar.org/graph/v1/paper/search"
#    VALID_SORT_CRITERIA: ClassVar[list[str]] = ["relevance", "citationCount", "publicationDate"]

#    def __init__(
#        self,
#        headers: dict[str, str] | None = None,
#    ) -> None:
#        """Initialize the Semantic Scholar retriever.

#        Args:
#            headers: Optional dictionary containing API configuration.
#                    Currently unused as Semantic Scholar has a free API.
#        """
#        super().__init__()
#        self.headers = headers or {}

#    def _get_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 20,
#        sort: str = "relevance",
#    ) -> list[Document]:
#        """Get documents relevant to a query using Semantic Scholar API.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 20.
#            sort: Sort criterion ('relevance', 'citationCount', 'publicationDate').
#                 Defaults to 'relevance'.

#        Returns:
#            List of relevant documents.

#        Raises:
#            ValueError: If sort criterion is invalid.
#        """
#        if sort.lower() not in self.VALID_SORT_CRITERIA:
#            raise ValueError(f"Invalid sort criterion. Must be one of {self.VALID_SORT_CRITERIA}")

#        logger.info(f"Searching with query {query}...")

#        params: dict[str, Any] = {
#            "query": query,
#            "limit": max_results,
#            "fields": "title,abstract,url,venue,year,authors,isOpenAccess,openAccessPdf",
#            "sort": sort.lower(),
#        }

#        try:
#            response = requests.get(self.BASE_URL, params=params)
#            response.raise_for_status()
#            results = response.json().get("data", [])
#        except Exception as e:
#            logger.exception(f"An error occurred while accessing Semantic Scholar API: {e.__class__.__name__}: {e}")
#            return []

#        documents: list[Document] = []

#        # Convert search results to Document objects
#        for result in results:
#            # Only include open access papers with PDF links
#            if result.get("isOpenAccess") and result.get("openAccessPdf"):
#                # Create Document object with metadata
#                doc = Document(
#                    page_content=result.get("abstract", "Abstract not available"),
#                    metadata={
#                        "title": result.get("title", "No Title"),
#                        "source": result["openAccessPdf"].get("url", "No URL"),
#                        "body": result.get("abstract", "Abstract not available"),
#                        "year": result.get("year"),
#                        "venue": result.get("venue"),
#                        "authors": [author.get("name") for author in result.get("authors", [])],
#                    },
#                )
#                documents.append(doc)

#        return documents

#    async def _aget_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 20,
#        sort: str = "relevance",
#    ) -> list[Document]:
#        """Asynchronously get documents relevant to a query using Semantic Scholar API.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 20.
#            sort: Sort criterion ('relevance', 'citationCount', 'publicationDate').
#                 Defaults to 'relevance'.

#        Returns:
#            List of relevant documents.

#        Raises:
#            ValueError: If sort criterion is invalid.
#        """
#        if sort.lower() not in self.VALID_SORT_CRITERIA:
#            raise ValueError(f"Invalid sort criterion. Must be one of {self.VALID_SORT_CRITERIA}")

#        logger.info(f"Searching with query {query}...")

#        params: dict[str, Any] = {
#            "query": query,
#            "limit": max_results,
#            "fields": "title,abstract,url,venue,year,authors,isOpenAccess,openAccessPdf",
#            "sort": sort.lower(),
#        }

#        try:
#            async with httpx.AsyncClient() as client:
#                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
#                response.raise_for_status()
#                results = response.json().get("data", [])
#        except Exception as e:
#            logger.exception(f"An error occurred while accessing Semantic Scholar API: {e.__class__.__name__}: {e}")
#            return []

#        documents: list[Document] = []

#        # Convert search results to Document objects
#        for result in results:
            # Only include open access papers with PDF links
#            if result.get("isOpenAccess") and result.get("openAccessPdf"):
                # Create Document object with metadata
#                doc = Document(
#                    page_content=result.get("abstract", "Abstract not available"),
#                    metadata={
#                        "title": result.get("title", "No Title"),
#                        "source": result["openAccessPdf"].get("url", "No URL"),
#                        "body": result.get("abstract", "Abstract not available"),
#                        "year": result.get("year"),
#                        "venue": result.get("venue"),
#                        "authors": [author.get("name") for author in result.get("authors", [])],
#                    },
#                )
#                documents.append(doc)

#        return documents


# =======


class SemanticScholarSearch:
    """Semantic Scholar API Retriever."""

    BASE_URL: ClassVar[str] = "https://api.semanticscholar.org/graph/v1/paper/search"
    VALID_SORT_CRITERIA: ClassVar[list[str]] = ["relevance", "citationCount", "publicationDate"]

    def __init__(
        self,
        query: str,
        sort: str = "relevance",
        query_domains: list[str] | None = None,
        *_: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ) -> None:
        """Initialize the SemanticScholarSearch class with a query and sort criterion.

        Args:
            query: Search query string
            sort: Sort criterion ('relevance', 'citationCount', 'publicationDate')
            query_domains: List of domains to search for
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.query: str = query
        assert sort in self.VALID_SORT_CRITERIA, "Invalid sort criterion"
        self.sort: str = sort.lower()
        self.query_domains: list[str] = [] if query_domains is None else query_domains

    def search(
        self,
        max_results: Optional[int] = None,
    ) -> list[dict[str, str]]:
        """
        Perform the search on Semantic Scholar and return results.

        Args:
            max_results: Maximum number of results to retrieve

        Returns:
            List of dictionaries containing title, href, and body of each paper
        """
        # If max_results is the default, check environment variable
        if max_results is None:
            max_results = int(os.environ.get("MAX_SOURCES", 20))
            
        logger.info(f"SemanticScholarSearch: Searching with query:{os.linesep*2}```{self.query}{os.linesep}```")

        params: dict[str, Any] = {
            "query": self.query,
            "limit": max_results,
            "fields": "title,abstract,url,venue,year,authors,isOpenAccess,openAccessPdf",
            "sort": self.sort,
        }

        try:
            response: requests.Response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"An error occurred while accessing Semantic Scholar API: {e}")
            return []

        results: list[dict[str, Any]] = cast(Dict[str, Any], response.json()).get("data", [])
        search_result: list[dict[str, str]] = []

        for result in results:
            if result.get("isOpenAccess") and result.get("openAccessPdf"):
                search_result.append(
                    {
                        "title": result.get("title", "No Title"),
                        "href": cast(Dict[str, Any], result["openAccessPdf"]).get("url", "No URL"),
                        "body": result.get("abstract", "Abstract not available"),
                    }
                )

        return search_result
