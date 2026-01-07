import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gpt_researcher.retrievers.internal_biblio.internal_biblio import InternalBiblioRetriever
from gpt_researcher.retrievers.tavily.tavily_search import TavilySearch

# --- Tavily Search Tests ---

@patch('requests.post')
def test_tavily_search_success(mock_post):
    """Test TavilySearch success scenario."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"url": "http://example.com/1", "content": "Content 1"},
            {"url": "http://example.com/2", "content": "Content 2"}
        ]
    }
    mock_post.return_value = mock_response

    retriever = TavilySearch(query="test", headers={"tavily_api_key": "test_key"})
    results = retriever.search()

    assert len(results) == 2
    assert results[0]["href"] == "http://example.com/1"
    assert results[0]["body"] == "Content 1"

@patch('requests.post')
def test_tavily_search_failure(mock_post):
    """Test TavilySearch failure scenario (exception)."""
    mock_post.side_effect = Exception("API Error")

    retriever = TavilySearch(query="test", headers={"tavily_api_key": "test_key"})
    # TavilySearch catches exceptions and returns empty list (and prints error)
    results = retriever.search()
    
    assert results == []

# --- Internal Biblio Tests ---

def test_internal_biblio_missing_user_id():
    """Test that InternalBiblioRetriever raises ValueError if user_id is missing."""
    with pytest.raises(ValueError, match="user_id is required"):
        InternalBiblioRetriever(query="test", headers={})

@patch('requests.post')
def test_internal_biblio_search_success(mock_post):
    """Test InternalBiblioRetriever search success."""
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "results": [
            {
                "metadata": {
                    "structured_data": {
                        "doi": "10.1234/test",
                        "title": "Test Title",
                        "year": 2023
                    }
                },
                "body": "Test Abstract"
            }
        ]
    }
    mock_post.return_value = mock_response

    headers = {"user_id": "123", "internal_api_base_url": "http://mock-api"}
    retriever = InternalBiblioRetriever(query="test", headers=headers)
    
    results = retriever.search()
    
    assert len(results) == 1
    assert results[0]["url"] == "https://doi.org/10.1234/test"
    assert "Test Title" in results[0]["title"]
    # Check that raw_content includes citation info
    assert "Citation: Test Title | 2023 | doi:10.1234/test" in results[0]["raw_content"]
    assert "Test Abstract" in results[0]["raw_content"]

@patch('requests.post')
def test_internal_biblio_search_failure(mock_post):
    """Test InternalBiblioRetriever network failure."""
    mock_post.side_effect = Exception("Connection Refused")
    
    headers = {"user_id": "123"}
    retriever = InternalBiblioRetriever(query="test", headers=headers)
    
    results = retriever.search()
    assert results == []
