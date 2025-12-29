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


class InternalBiblioRetriever:
    """
    Internal API Retriever for accessing user-specific bibliographic data.
    
    This retriever connects to an internal API endpoint to retrieve:
    - Bibliographic data (type=biblio)
    - Highlights/notes (type=highlight)
    - PDF fragments (type=File)
    
    The user_id must be provided in the headers when initializing the retriever.
    """

    def __init__(
        self, 
        query: str, 
        headers: Optional[Dict[str, str]] = None,
        query_domains: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the Internal Biblio Retriever.

        Args:
            query (str): The search query string.
            headers (dict, optional): Headers containing user_id and other configuration.
                Expected keys:
                - user_id: The user ID for accessing user-specific data
                - internal_api_base_url: Optional base URL for the internal API
                    (default: http://unob.ivy:8080)
                - internal_api_type: Optional type parameter (biblio, highlight, or File)
                    (default: biblio)
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
                "user_id is required in headers for InternalBiblioRetriever. "
                "Please provide user_id in the headers when making the request."
            )
        
        # Get API base URL from headers or environment variable, with default
        self.base_url = (
            self.headers.get("internal_api_base_url") or
            os.getenv("INTERNAL_API_BASE_URL", "http://unob.ivy:8080")
        )
        
        # Get type from headers or use default
        self.search_type = self.headers.get("internal_api_type", "biblio")
        
        # Validate type
        valid_types = ["biblio", "highlight", "File"]
        if self.search_type not in valid_types:
            logger.warning(
                f"Invalid type '{self.search_type}'. Valid types are: {valid_types}. "
                f"Using default 'biblio'."
            )
            self.search_type = "biblio"
        
        # Construct the API endpoint
        self.endpoint = f"{self.base_url}/internal/biblios/semantic_search/"
        
        logger.info(
            f"Initialized InternalBiblioRetriever with user_id={self.user_id}, "
            f"type={self.search_type}, endpoint={self.endpoint}"
        )

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
            
            # Make the API request
            response = requests.get(
                self.endpoint,
                params=params,
                timeout=30  # 30 second timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Transform the response to match the expected format
            # The API response format may vary, so we handle different structures
            results = self._transform_response(data)
            
            logger.info(f"Retrieved {len(results)} results from internal API")
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve search results from internal API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in InternalBiblioRetriever.search: {e}")
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
        
        # Try to extract href/url/id (required)
        href = (
            item.get("href") or
            item.get("url") or
            item.get("id") or
            item.get("source") or
            item.get("link") or
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
        
        # If href looks like an ID (not a URL), we can optionally format it
        # For internal biblios, IDs are typically used as-is
        # The href will be displayed in references as: [id](id)
        # If you want a clickable link, provide a full URL in the href field
        
        return {
            "href": href_str,
            "body": str(body)
        }

