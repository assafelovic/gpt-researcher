"""
Internal Biblio Retriever

A retriever that accesses internal API for bibliographic data, highlights, and PDF fragments.
Supports different types: biblio, highlight, and File.
"""
from typing import Any, Dict, List, Optional
import requests
import os
import logging

logger = logging.getLogger(__name__)


class BaseInternalBiblioRetriever:
    """
    Base class for Internal API Retrievers.
    
    This base class provides common functionality for accessing user-specific data
    from the internal API. Subclasses should set the search_type attribute.
    """

    def __init__(
        self, 
        query: str, 
        headers: Optional[Dict[str, str]] = None,
        query_domains: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the Base Internal Biblio Retriever.

        Args:
            query (str): The search query string.
            headers (dict, optional): Headers containing user_id and other configuration.
                Expected keys:
                - user_id: The user ID for accessing user-specific data
                - internal_api_base_url: Optional base URL for the internal API
                    (default: http://unob.ivy:8080)
            query_domains (list, optional): List of domains to search (not used).
            **kwargs: Additional arguments (for compatibility).
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        
        # Get user_id from headers
        self.user_id = self.headers.get("user_id")
        if not self.user_id:
            raise ValueError(
                f"user_id is required in headers for {self.__class__.__name__}. "
                "Please provide user_id in the headers when making the request."
            )
        
        # Get API base URL from headers or environment variable, with default
        self.base_url = (
            self.headers.get("internal_api_base_url") or
            os.getenv("INTERNAL_API_BASE_URL", "https://www.ivysci.com")
        )
        
        # Get API key from headers or environment variable
        self.api_key = (
            self.headers.get("internal_api_key") or
            os.getenv("INTERNAL_API_KEY")
        )
        
        # Construct the API endpoint
        base = str(self.base_url).rstrip("/")
        # Current internal API expects: POST /api/v2/internal/biblios/vector_search/
        self.endpoint = f"{base}/internal/biblios/vector_search/"
        
        logger.info(
            f"Initialized {self.__class__.__name__} with user_id={self.user_id}, "
            f"type={self.search_type}, endpoint={self.endpoint}"
        )

    @property
    def search_type(self) -> str:
        """
        Subclasses must override this property to specify the search type.
        """
        raise NotImplementedError("Subclasses must implement search_type property")

    def search(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Performs the search using the internal API endpoint.

        Args:
            max_results (int): Maximum number of results to return (not currently used by API).

        Returns:
            List of search results in the format:
            [
                {
                    "href": "source_url_or_id",
                    "body": "content_text"
                },
                ...
            ]
        """
        try:
            # Determine request type:
            # - allow callers to override via headers["internal_api_type"]
            # - normalize to match internal API enum expectations (commonly lowercase)
            req_type = self.headers.get("internal_api_type") or self.search_type
            if isinstance(req_type, str):
                req_type = req_type.strip()
                req_type = req_type.lower()

            # Prepare request parameters
            params = {
                "type": req_type,
                "user_id": self.user_id,
                "query": self.query
            }
            
            logger.info(
                f"Searching internal API: {self.endpoint} with params: "
                f"type={self.search_type}, user_id={self.user_id}, query={self.query[:50]}..."
            )
            
            # Prepare request headers
            request_headers = {}
            if self.api_key:
                request_headers["x-api-key"] = self.api_key
            
            # Make the API request
            # Internal API expects POST (JSON body). Do not fall back to GET.
            response = requests.post(
                self.endpoint,
                json=params,
                headers=request_headers,
                timeout=30  # 30 second timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Transform the response to match the expected format
            # The API response format may vary, so we handle different structures
            results = self._transform_response(data)
            
            logger.info(f"Retrieved {len(results)} results from internal API (type={self.search_type})")
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve search results from internal API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.search: {e}")
            return []

    def _transform_response(self, data: Any) -> List[Dict[str, Any]]:
        """
        Transform the API response to the expected format.
        
        The expected format is:
        [
            {
                "href": "source_url_or_id",  # Required: href, url, or id field
                "body": "content_text"       # Required: body, content, or text field
            },
            ...
        ]
        
        This method handles different possible response structures from the API.
        
        Args:
            data: The JSON response from the API
            
        Returns:
            List of transformed results
            
        Note:
            Each result item must have:
            - An identifier field: href, url, or id
            - A content field: body, content, or text
            Items missing either field will be skipped with a warning.
        """
        results = []
        
        # Handle different response structures
        if isinstance(data, list):
            # If response is directly a list
            for item in data:
                result = self._transform_item(item)
                if result:
                    results.append(result)
        elif isinstance(data, dict):
            # If response is a dict, look for common keys
            if "results" in data:
                items = data["results"]
            elif "data" in data:
                items = data["data"]
            elif "items" in data:
                items = data["items"]
            else:
                # Try to use the dict itself as a single result
                items = [data]
            
            for item in items:
                result = self._transform_item(item)
                if result:
                    results.append(result)
        else:
            logger.warning(f"Unexpected response format: {type(data)}")
        
        return results

    def _transform_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """
        Transform a single item from the API response.
        
        Subclasses can override this method to handle different field mappings
        for different types (biblio, highlight, File).
        
        Args:
            item: A single item from the API response
            
        Returns:
            Transformed item dict or None if transformation fails
            
        Note:
            Each item must have:
            - href/id field: identifier or URL for the source
            - body/content/text field: the actual content text
        """
        if not isinstance(item, dict):
            return None

        # Many internal endpoints (e.g. vector_search) return:
        # { "content": "...", "metadata": {...}, "score": ... }
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        structured = metadata.get("structured_data")
        if not isinstance(structured, dict):
            structured = {}
        
        # Try to extract href/url/id (required)
        # Prefer DOI link if available (most useful stable identifier)
        doi = structured.get("doi")
        if isinstance(doi, str):
            doi = doi.strip()
        if doi:
            href = f"https://doi.org/{doi}"
        else:
            href = (
            item.get("href") or
            item.get("url") or
            item.get("id") or
            item.get("source") or
            item.get("link") or
            # Internal IDs commonly live under metadata
            metadata.get("biblio_id") or
            metadata.get("highlight_id") or
            metadata.get("file_id") or
            metadata.get("doc_id") or
            metadata.get("document_id") or
            metadata.get("id") or
            None
            )
        
        # Try to extract body/content/text (required)
        body = (
            item.get("body") or
            item.get("content") or
            item.get("text") or
            item.get("abstract") or
            item.get("description") or
            item.get("snippet") or
            # Some internal endpoints use metadata for text fields, too
            metadata.get("content") or
            metadata.get("text") or
            None
        )
        
        # Both href/id and body/content/text are required
        if not body:
            logger.warning(
                f"Item missing content field (body/content/text). "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        if not href:
            logger.warning(
                f"Item missing identifier field (href/url/id). "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        # Convert href to string and format for display
        href_str = str(href)

        # If we only have a biblio_id and no DOI, provide a deterministic (but possibly non-resolvable) URL
        if href_str.isdigit():
            try:
                biblio_id = metadata.get("biblio_id")
                if biblio_id is not None:
                    href_str = f"https://www.ivysci.com/biblio/{biblio_id}"
            except Exception:
                pass
        
        # If href looks like an ID (not a URL), we can optionally format it
        # For internal biblios, IDs are typically used as-is
        # The href will be displayed in references as: [id](id)
        # If you want a clickable link, provide a full URL in the href field
        
        title = (
            structured.get("title")
            or metadata.get("title")
            or structured.get("paper_title")
            or ""
        )
        year = structured.get("year") if isinstance(structured.get("year"), (str, int)) else ""
        doi_for_note = structured.get("doi") if isinstance(structured.get("doi"), str) else ""
        citation_hint_parts = []
        if title:
            citation_hint_parts.append(str(title))
        if year:
            citation_hint_parts.append(str(year))
        if doi_for_note:
            citation_hint_parts.append(f"doi:{doi_for_note.strip()}")
        citation_hint = " | ".join([p for p in citation_hint_parts if p]).strip()
        if citation_hint:
            raw_content = f"Citation: {citation_hint}\n\n{str(body)}"
        else:
            raw_content = str(body)

        # IMPORTANT: downstream context compressors expect SearchAPI-shaped keys:
        # - url/raw_content/title (see gpt_researcher/context/retriever.py)
        return {
            "url": href_str,
            "title": str(title) if title is not None else "",
            "raw_content": raw_content,
            # Internal vector_search results already contain the relevant content;
            # avoid treating url as a URL to be scraped again.
            "skip_scrape": True,
        }


class InternalBiblioRetriever(BaseInternalBiblioRetriever):
    """
    Internal API Retriever for bibliographic data (type=biblio).
    
    This retriever connects to an internal API endpoint to retrieve bibliographic data.
    The user_id must be provided in the headers when initializing the retriever.
    """
    
    @property
    def search_type(self) -> str:
        return "biblio"


class InternalHighlightRetriever(BaseInternalBiblioRetriever):
    """
    Internal API Retriever for highlights/notes (type=highlight).
    
    This retriever connects to an internal API endpoint to retrieve user highlights and notes.
    The user_id must be provided in the headers when initializing the retriever.
    """
    
    @property
    def search_type(self) -> str:
        return "highlight"


class InternalFileRetriever(BaseInternalBiblioRetriever):
    """
    Internal API Retriever for PDF fragments (type=File).
    
    This retriever connects to an internal API endpoint to retrieve PDF fragments.
    The user_id must be provided in the headers when initializing the retriever.
    """
    
    @property
    def search_type(self) -> str:
        return "file"
