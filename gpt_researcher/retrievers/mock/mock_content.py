from ..base import BaseRetriever
from typing import List, Dict, Any

class MockContentRetriever(BaseRetriever):
    """Example retriever that returns content directly without scraping"""
    
    @property
    def requires_scraping(self) -> bool:
        return False
        
    def search(self, max_results: int = 7) -> List[Dict[str, Any]]:
        """Returns mock research content directly"""
        mock_data = [
            {
                "body": "Mock research paper about AI advances in 2024. This paper discusses...",
                "title": "AI Advances 2024",
                "metadata": {"author": "Mock Researcher", "year": 2024}
            },
            {
                "body": "Study on climate change impacts in urban areas. The findings suggest...", 
                "title": "Climate Change Urban Impact",
                "metadata": {"author": "Mock Scientist", "year": 2024}
            }
        ]
        return mock_data[:max_results] 