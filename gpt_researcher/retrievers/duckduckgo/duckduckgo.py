from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any

from gpt_researcher.utils import check_pkg
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.retrievers.retriever_abc import RetrieverABC

if TYPE_CHECKING:
    import logging

    from duckduckgo_search import DDGS

logger: logging.Logger = get_formatted_logger(__name__)


# class Duckduckgo(BaseRetriever):
#     """DuckDuckGo Search Retriever that implements LangChain's BaseRetriever interface."""

#     def __init__(self) -> None:
#         """Initialize the DuckDuckGo retriever.

#         Raises:
#             ImportError: If duckduckgo_search package is not installed.
#         """
#         super().__init__()
#         check_pkg("duckduckgo_search")
#         from duckduckgo_search import DDGS

#         self.ddg: DDGS = DDGS()

#     def _get_relevant_documents(
#         self,
#         query: str,
#         *,
#         run_manager: CallbackManagerForRetrieverRun,
#         max_results: int = 5,
#     ) -> list[Document]:
#         """Get documents relevant to a query using DuckDuckGo Search.

#         Args:
#             query: The search query string.
#             run_manager: Callback manager for the retriever run.
#             max_results: Maximum number of results to return. Defaults to 5.

#         Returns:
#             List of relevant documents.
#         """
#         logger.info(f"Searching with query {query}...")

#         try:
#             search_results: list[dict[str, str]] = self.ddg.text(
#                 query,
#                 region="wt-wt",
#                 max_results=max_results,
#             )
#         except Exception as e:
#             logger.exception(f"Failed fetching sources. Resulting in empty response: {e.__class__.__name__}: {e}")
#             return []

#         documents: list[Document] = []

#         # Convert search results to Document objects
#         for result in search_results:
# Create Document object with metadata
#            doc = Document(
#                page_content=result["body"],
#                metadata={
#                    "title": result["title"],
#                    "source": result["link"],
#                },
#            )
#            documents.append(doc)

#         return documents

#     async def _aget_relevant_documents(
#         self,
#         query: str,
#         *,
#         run_manager: CallbackManagerForRetrieverRun,
#         max_results: int = 5,
#     ) -> list[Document]:
#         """Asynchronously get documents relevant to a query using DuckDuckGo Search.

#         Args:
#             query: The search query string.
#             run_manager: Callback manager for the retriever run.
#             max_results: Maximum number of results to return. Defaults to 5.

#         Returns:
#             List of relevant documents.
#         """
#         logger.info(f"Searching with query {query}...")

#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(
#                     "https://api.duckduckgo.com/",
#                     params={
#                         "q": query,
#                         "format": "json",
#                         "no_html": 1,
#                         "no_redirect": 1,
#                         "kl": "wt-wt",  # Region
#                     },
#                 )
#                 response.raise_for_status()
#                 search_results = response.json()
#         except Exception as e:
#             logger.exception(f"Failed fetching sources. Resulting in empty response: {e.__class__.__name__}: {e}")
#             return []

#         documents: list[Document] = []

#         # Convert search results to Document objects
#         for result in search_results.get("RelatedTopics", [])[:max_results]:
#             if "Text" in result and "FirstURL" in result:
#                 doc = Document(
#                     page_content=result["Text"],
#                     metadata={
#                         "title": result.get("Text", "").split(" - ")[0],
#                         "source": result["FirstURL"],
#                     },
#                 )
#                 documents.append(doc)

#         return documents


class Duckduckgo(RetrieverABC):
    """Duckduckgo API Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        *args: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        check_pkg("duckduckgo_search")
        from duckduckgo_search import DDGS

        self.ddg: DDGS = DDGS()
        self.query: str = query
        self.query_domains: list[str] = [] if query_domains is None else query_domains
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

    def search(
        self,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """Searches the query.

        Useful for general internet search queries using DuckDuckGo.

        Returns:
            list[dict[str, str]]: The search results.
        """
        # TODO: Add support for query domains
        # If max_results is the default, check environment variable
        if max_results is None:
            max_results = int(os.environ.get("MAX_SOURCES", 10))

        logger.info(f"Duckduckgo: Searching with query:{os.linesep*2}```{self.query}{os.linesep}```")

        try:
            search_response: list[dict[str, str]] = self.ddg.text(self.query, region="wt-wt", max_results=max_results)
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []
        return search_response
