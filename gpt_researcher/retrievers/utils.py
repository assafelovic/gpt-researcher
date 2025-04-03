import importlib.util
import os
import requests
from typing import Dict, Any, Optional, Union, Callable
import json
import logging
import time
from functools import wraps
from collections import defaultdict

VALID_RETRIEVERS = [
    "arxiv",
    "bing",
    "custom",
    "duckduckgo",
    "exa",
    "google",
    "searchapi",
    "searx",
    "semantic_scholar",
    "serpapi",
    "serper",
    "tavily",
    "pubmed_central",
]

# Store the last request time for each domain
_last_request_times = defaultdict(float)

def rate_limit(domain: str, requests_per_minute: int = 10):
    """
    Decorator for rate limiting API requests to specific domains.
    
    Args:
        domain (str): The domain to rate limit
        requests_per_minute (int): Maximum requests allowed per minute
        
    Returns:
        Callable: Decorated function with rate limiting
    """
    min_interval = 60.0 / requests_per_minute
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global _last_request_times
            
            # Calculate time since last request
            current_time = time.time()
            time_since_last_request = current_time - _last_request_times[domain]
            
            # If we need to wait to respect the rate limit
            if time_since_last_request < min_interval:
                sleep_time = min_interval - time_since_last_request
                logging.debug(f"Rate limiting {domain}: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Update the last request time
            _last_request_times[domain] = time.time()
            
            # Call the original function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def check_pkg(pkg: str) -> None:
    if not importlib.util.find_spec(pkg):
        pkg_kebab = pkg.replace("_", "-")
        raise ImportError(
            f"Unable to import {pkg_kebab}. Please install with "
            f"`pip install -U {pkg_kebab}`"
        )

# Get a list of all retriever names to be used as validators for supported retrievers
def get_all_retriever_names() -> list:
    try:
        current_dir = os.path.dirname(__file__)

        all_items = os.listdir(current_dir)

        # Filter out only the directories, excluding __pycache__
        retrievers = [item for item in all_items if os.path.isdir(os.path.join(current_dir, item))]
    except Exception as e:
        print(f"Error in get_all_retriever_names: {e}")
        retrievers = VALID_RETRIEVERS
    
    return retrievers

def normalize_search_results(results, max_results=10):
    """
    Normalizes search results to a consistent format across different retrievers.
    
    Args:
        results (list): List of search result dictionaries
        max_results (int, optional): Maximum number of results to return. Defaults to 10.
        
    Returns:
        list: Normalized search results with consistent keys
    """
    normalized_results = []
    
    if not results or not isinstance(results, list):
        return normalized_results
        
    for result in results[:max_results]:
        if not isinstance(result, dict):
            continue
            
        normalized_result = {
            "title": result.get("title", ""),
            "href": result.get("href", result.get("url", "")),
            "body": result.get("body", result.get("content", result.get("snippet", ""))),
        }
        
        # Skip results with empty URLs
        if not normalized_result["href"]:
            continue
            
        # Ensure we have at least some content
        if not normalized_result["body"] and not normalized_result["title"]:
            continue
            
        normalized_results.append(normalized_result)
        
    return normalized_results

def safe_request(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    max_retries: int = 2,
    json_data: Optional[Dict[str, Any]] = None
) -> Optional[requests.Response]:
    """
    Makes a safe HTTP request with retry logic and proper error handling.
    
    Args:
        url (str): The URL to make the request to
        method (str, optional): The HTTP method to use. Defaults to "GET".
        params (Dict[str, Any], optional): Query parameters to include. Defaults to None.
        data (Dict[str, Any] or str, optional): Form data or raw body. Defaults to None.
        headers (Dict[str, str], optional): HTTP headers. Defaults to None.
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
        max_retries (int, optional): Maximum number of retry attempts. Defaults to 2.
        json_data (Dict[str, Any], optional): JSON data to send. Defaults to None.
        
    Returns:
        Optional[requests.Response]: The response object or None if the request failed
    """
    headers = headers or {}
    
    # Convert JSON data to string if provided
    if json_data is not None and isinstance(json_data, dict):
        data = json.dumps(json_data)
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
    
    # Try the request with retries
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=timeout
            )
            
            # Check for successful response
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                logging.warning(f"Request failed: {e}. Retrying {attempt+1}/{max_retries}...")
                continue
            else:
                logging.error(f"Request failed after {max_retries} retries: {e}")
                return None
    
    return None
