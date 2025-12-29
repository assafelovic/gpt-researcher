"""
NoteExpress Retriever

A retriever that accesses NoteExpress API for academic paper search using semantic search.
"""
from typing import Any, Dict, List, Optional
import httpx
import os
import logging

logger = logging.getLogger(__name__)


class NoteExpressRetriever:
    """
    NoteExpress API Retriever for accessing academic papers via semantic search.
    
    This retriever connects to the NoteExpress API endpoint to retrieve academic papers
    using semantic search. It returns papers with DOI links and formatted content.
    """

    def __init__(
        self, 
        query: str, 
        headers: Optional[Dict[str, str]] = None,
        query_domains: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the NoteExpress Retriever.

        Args:
            query (str): The search query string.
            headers (dict, optional): Headers containing API configuration.
                Expected keys:
                - noteexpress_api_key: Optional API key for authentication
                - noteexpress_base_url: Optional base URL for the API
                    (default: https://service.inoteexpress.com/papers-graph-backend)
            query_domains (list, optional): List of domains to search (not used).
            **kwargs: Additional arguments (for compatibility).
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        
        # Get API key from headers or environment variable
        api_key = (
            self.headers.get("noteexpress_api_key") or
            os.getenv("NOTEEXPRESS_API_KEY")
        )
        
        # Get base URL from headers or environment variable, with default
        base_url = (
            self.headers.get("noteexpress_base_url") or
            os.getenv("NOTEEXPRESS_BASE_URL", "https://service.inoteexpress.com/papers-graph-backend")
        )
        
        # Store configuration for client creation
        self.api_key = api_key
        self.base_url = base_url
        self.client_headers = {"Accept": "application/json, text/plain, */*"}
        if api_key:
            self.client_headers["Authorization"] = f"Bearer {api_key}"
        
        logger.info(
            f"Initialized NoteExpressRetriever with base_url={base_url}, "
            f"has_api_key={bool(api_key)}"
        )

    def search(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Performs semantic search using the NoteExpress API endpoint.

        Args:
            max_results (int): Maximum number of results to return (max 20).

        Returns:
            List of search results in the format:
            [
                {
                    "href": "https://doi.org/{doi}",
                    "body": "Authors: ... | Title: ... | Abstract: ..."
                },
                ...
            ]
        """
        # Use context manager to ensure proper resource cleanup
        with httpx.Client(
            base_url=self.base_url,
            headers=self.client_headers,
            proxy=None,  # 明确不使用 proxy
            trust_env=False,  # 不信任环境变量中的 proxy 设置
            timeout=httpx.Timeout(30.0, connect=5.0),  # 语义搜索可能需要更长时间
        ) as client:
            try:
                # Prepare request parameters
                url = "/api/papers/search/semantic"
                params = {
                    "query": self.query.strip(),
                    "limit": min(max_results, 20),  # API 最多只支持 20 条
                }
                
                logger.info(
                    f"Searching NoteExpress API: {url} with query: {self.query[:50]}..."
                )
                
                # Make the API request
                response = client.get(url, params=params)
                response.raise_for_status()
                
                # Parse the response
                resp_data = response.json()
                
                # Extract papers from response (expected format: {"papers": [...]})
                papers = resp_data.get("papers", [])
                
                # Transform the response to match the expected format
                results = []
                for paper_data in papers:
                    result = self._transform_paper(paper_data)
                    if result:
                        results.append(result)
                
                logger.info(f"Retrieved {len(results)} results from NoteExpress API")
                
                return results
                
            except httpx.RequestError as e:
                logger.error(f"Failed to retrieve search results from NoteExpress API: {e}")
                return []
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from NoteExpress API: {e.response.status_code} - {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error in NoteExpressRetriever.search: {e}")
                return []

    def _transform_paper(self, paper_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transform a single paper from the API response.
        
        Args:
            paper_data: A single paper dictionary from the API
            
        Returns:
            Transformed paper dict with href and body, or None if transformation fails
        """
        if not isinstance(paper_data, dict):
            return None
        
        # Extract DOI for href
        doi = paper_data.get("doi", "").strip()
        if doi:
            href = f"https://doi.org/{doi}"
        else:
            # If no DOI, try to use other identifiers
            # For now, we'll skip papers without DOI
            logger.debug(f"Paper missing DOI, skipping. Title: {paper_data.get('title', 'Unknown')[:50]}")
            return None
        
        # Extract title
        title = paper_data.get("title", "").strip()
        if not title:
            logger.debug("Paper missing title, skipping")
            return None
        
        # Extract authors
        authors = paper_data.get("authors", [])
        authors_str = ""
        if authors and isinstance(authors, list):
            # Format authors list
            author_names = [str(a) for a in authors if a]
            if author_names:
                authors_str = ", ".join(author_names)
        
        # Extract abstract
        abstract = paper_data.get("abstract", "").strip()
        
        # Build body: Authors | Title | Abstract
        body_parts = []
        if authors_str:
            body_parts.append(f"Authors: {authors_str}")
        if title:
            body_parts.append(f"Title: {title}")
        if abstract:
            body_parts.append(f"Abstract: {abstract}")
        
        body = "\n".join(body_parts)
        
        if not body:
            logger.debug("Paper missing all content fields, skipping")
            return None
        
        return {
            "href": href,
            "body": body
        }

