from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseRetriever(ABC):
    """Base class for all retrievers"""
    
    def __init__(self, query: str, headers: Dict = None):
        self.query = query
        self.headers = headers or {}
        
    @property
    def requires_scraping(self) -> bool:
        """Whether this retriever returns URLs that need scraping"""
        return True
    
    @abstractmethod
    def search(self, max_results: int = 7) -> List[Dict[str, Any]]:
        """
        Search method that all retrievers must implement
        
        Returns:
            For requires_scraping=True: List of dicts with 'href' key containing URLs
            For requires_scraping=False: List of dicts with 'body' key containing content
        """
        pass 