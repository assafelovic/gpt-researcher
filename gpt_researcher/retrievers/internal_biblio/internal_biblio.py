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
        self.endpoint = f"{self.base_url}/internal/biblios/semantic_search/"
        
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
            # Prepare request parameters
            params = {
                "type": self.search_type,
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
            response = requests.get(
                self.endpoint,
                params=params,
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
        
        Subclasses must implement this method to handle different field mappings
        for different types (biblio, highlight, File).
        
        Args:
            item: A single item from the API response
            
        Returns:
            Transformed item dict or None if transformation fails
            
        Note:
            Each item must have:
            - href: URL in format https://www.ivysci.com/biblio/{biblio_id}
            - body: Combined title + content text
        """
        raise NotImplementedError("Subclasses must implement _transform_item method")


class InternalBiblioRetriever(BaseInternalBiblioRetriever):
    """
    Internal API Retriever for bibliographic data (type=biblio).
    
    This retriever connects to an internal API endpoint to retrieve bibliographic data.
    The user_id must be provided in the headers when initializing the retriever.
    """
    
    @property
    def search_type(self) -> str:
        return "biblio"
    
    def _transform_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """
        Transform a biblio item from the API response.
        
        Expected format:
        {
            "content": "...",
            "metadata": {
                "biblio_id": 123,
                "structured_data": {
                    "title": "...",
                    ...
                }
            }
        }
        
        Returns:
            {
                "href": "https://www.ivysci.com/biblio/{biblio_id}",
                "body": "{title}\n\n{content}"
            }
        """
        if not isinstance(item, dict):
            return None
        
        # Extract biblio_id from metadata
        metadata = item.get("metadata", {})
        biblio_id = metadata.get("biblio_id")
        
        if not biblio_id:
            logger.warning(
                f"Biblio item missing biblio_id in metadata. "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        # Extract title from metadata.structured_data.title
        structured_data = metadata.get("structured_data", {})
        title = structured_data.get("title", "")
        
        # Extract content
        content = item.get("content", "")
        
        if not content:
            logger.warning(
                f"Biblio item missing content field. "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        # Combine title and content
        if title:
            body = f"{title}\n\n{content}"
        else:
            body = content
        
        # Format href
        href = f"https://www.ivysci.com/biblio/{biblio_id}"
        
        return {
            "href": href,
            "body": body
        }


class InternalHighlightRetriever(BaseInternalBiblioRetriever):
    """
    Internal API Retriever for highlights/notes (type=highlight).
    
    This retriever connects to an internal API endpoint to retrieve user highlights and notes.
    The user_id must be provided in the headers when initializing the retriever.
    """
    
    @property
    def search_type(self) -> str:
        return "highlight"
    
    def _transform_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """
        Transform a highlight item from the API response.
        
        Expected format:
        {
            "content": "**高亮内容**: ...\n**笔记**: ...",
            "metadata": {
                "biblio_id": 123,
                "highlight_id": 456
            }
        }
        
        Returns:
            {
                "href": "https://www.ivysci.com/biblio/{biblio_id}",
                "body": "{content}"
            }
        """
        if not isinstance(item, dict):
            return None
        
        # Extract biblio_id from metadata
        metadata = item.get("metadata", {})
        biblio_id = metadata.get("biblio_id")
        
        if not biblio_id:
            logger.warning(
                f"Highlight item missing biblio_id in metadata. "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        # Extract content (contains highlight and note)
        content = item.get("content", "")
        
        if not content:
            logger.warning(
                f"Highlight item missing content field. "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        # Format href
        href = f"https://www.ivysci.com/biblio/{biblio_id}"
        
        # For highlights, content already contains formatted text (高亮内容 + 笔记)
        # No need to add title, use content as-is
        return {
            "href": href,
            "body": content
        }


class InternalFileRetriever(BaseInternalBiblioRetriever):
    """
    Internal API Retriever for PDF fragments (type=File).
    
    This retriever connects to an internal API endpoint to retrieve PDF fragments.
    The user_id must be provided in the headers when initializing the retriever.
    """
    
    @property
    def search_type(self) -> str:
        return "File"
    
    def _transform_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """
        Transform a file item from the API response.
        
        Expected format:
        {
            "content": "...",
            "metadata": {
                "biblio_id": 123,
                "Header 1": "标题",
                ...
            }
        }
        
        Returns:
            {
                "href": "https://www.ivysci.com/biblio/{biblio_id}",
                "body": "{Header 1}\n\n{content}"
            }
        """
        if not isinstance(item, dict):
            return None
        
        # Extract biblio_id from metadata
        metadata = item.get("metadata", {})
        biblio_id = metadata.get("biblio_id")
        
        if not biblio_id:
            logger.warning(
                f"File item missing biblio_id in metadata. "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        # Extract title from metadata["Header 1"]
        title = metadata.get("Header 1", "")
        
        # Extract content
        content = item.get("content", "")
        
        if not content:
            logger.warning(
                f"File item missing content field. "
                f"Item keys: {list(item.keys())}. Skipping item."
            )
            return None
        
        # Combine title and content
        if title:
            body = f"{title}\n\n{content}"
        else:
            body = content
        
        # Format href
        href = f"https://www.ivysci.com/biblio/{biblio_id}"
        
        return {
            "href": href,
            "body": body
        }
