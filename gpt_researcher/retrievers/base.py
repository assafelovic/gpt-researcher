from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

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
            For requires_scraping=True: 
                List[Dict] with keys:
                - 'href': str (URL to be scraped)
                
            For requires_scraping=False:
                List[Dict] with keys:
                - 'source': str (identifier of the content source)
                - 'raw_content': str (the actual content)
                - 'title': str (title of the content)
                - 'image_urls': List[str] (optional, list of related image URLs)
        """
        pass 