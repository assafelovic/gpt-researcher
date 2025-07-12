#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, '.')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Look for .env file in current directory and parent directories
    env_file = None
    current_dir = Path('.')
    for parent in [current_dir] + list(current_dir.parents):
        potential_env = parent / '.env'
        if potential_env.exists():
            env_file = potential_env
            break

    if env_file:
        load_dotenv(env_file)
        print(f"Loaded .env from: {env_file.absolute()}")
    else:
        print("No .env file found, checking for .env.example...")
        # Try .env.example as fallback
        example_env = current_dir / '.env.example'
        if example_env.exists():
            print(f"Found .env.example at: {example_env.absolute()}")
            print("Please copy .env.example to .env and add your API keys")
        else:
            print("No .env or .env.example file found")

except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
    print("Proceeding with system environment variables only...")

print("\n=== Environment Check ===")
print(f"Current working directory: {Path.cwd()}")
print(f"RETRIEVER: {os.environ.get('RETRIEVER', 'Not set')}")
print(f"TAVILY_API_KEY: {'Set' if os.environ.get('TAVILY_API_KEY') else 'Not set'}")
print(f"OPENAI_API_KEY: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Not set'}")

print("\n=== Config Check ===")
try:
    from gpt_researcher.config.config import Config
    cfg = Config()
    print(f"cfg.retrievers: {cfg.retrievers}")
    print(f"cfg.retriever: {getattr(cfg, 'retriever', 'Not set')}")
except Exception as e:
    print(f"Config error: {e}")

print("\n=== Retriever Classes Check ===")
try:
    from gpt_researcher.actions.retriever import get_retrievers
    headers = {}
    retrievers = get_retrievers(headers, cfg)
    print(f"Retrieved classes: {[r.__name__ if hasattr(r, '__name__') else str(r) for r in retrievers]}")
except Exception as e:
    print(f"Retriever classes error: {e}")

print("\n=== Tavily Test ===")
try:
    from gpt_researcher.retrievers.tavily.tavily_search import TavilySearch
    tavily = TavilySearch('test query')
    print(f"Tavily API key: {'Found' if tavily.api_key else 'Missing'}")

    # Try a simple search
    print("Attempting search...")
    results = tavily.search(max_results=1)
    print(f"Search results: {len(results)} items")
    if results:
        print(f"First result keys: {list(results[0].keys())}")
except Exception as e:
    print(f"Tavily test error: {e}")

print("\n=== DuckDuckGo Fallback Test ===")
try:
    from gpt_researcher.retrievers.duckduckgo.duckduckgo import Duckduckgo
    ddg = Duckduckgo('test query')
    print("DuckDuckGo initialized successfully")

    # Try a simple search
    print("Attempting DuckDuckGo search...")
    results = ddg.search(max_results=1)
    print(f"DuckDuckGo search results: {len(results)} items")
    if results:
        print(f"First result keys: {list(results[0].keys())}")
except Exception as e:
    print(f"DuckDuckGo test error: {e}")

print("\n=== Search Results Integration Test ===")
try:
    from gpt_researcher.actions.query_processing import get_search_results

    print("Testing search results with fallback mechanism...")
    if 'retrievers' in locals():
        primary_retriever = retrievers[0]
        fallback_retrievers = retrievers[1:] if len(retrievers) > 1 else None

        print(f"Primary retriever: {primary_retriever.__name__}")
        print(f"Fallback retrievers: {[r.__name__ for r in fallback_retrievers] if fallback_retrievers else 'None'}")

        # This is an async function, so we need to run it properly
        import asyncio

        async def test_search():
            try:
                results = await get_search_results(
                    "test query",
                    primary_retriever,
                    fallback_retrievers=fallback_retrievers,
                    min_results=1
                )
                return results
            except Exception as e:
                return f"Search error: {e}"

        search_results = asyncio.run(test_search())
        if isinstance(search_results, list):
            print(f"Integrated search results: {len(search_results)} items")
        else:
            print(f"Integrated search error: {search_results}")
    else:
        print("No retrievers available for testing")

except Exception as e:
    print(f"Integration test error: {e}")
