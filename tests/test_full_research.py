#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys

from pathlib import Path
from typing import Any

# Add current directory to Python path
sys.path.insert(0, '.')

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded .env from: {env_file.absolute()}")
except ImportError:
    print("python-dotenv not available, using system environment")

async def test_research() -> bool:
    """Test the full research pipeline with fallback retrievers."""
    print("=== Testing Full Research Pipeline ===")

    try:
        from gpt_researcher.agent import GPTResearcher

        # Create a simple research query
        query = "What are the benefits of renewable energy?"

        print(f"Research query: '''{query}'''")
        print("Initializing GPT Researcher...")

        # Initialize researcher
        researcher = GPTResearcher(
            query=query,
            report_type="research_report",
            verbose=True
        )

        print(f"Configured retrievers: {[r.__name__ for r in researcher.retrievers]}")

        # Test search functionality
        print("\n=== Testing Search ===")
        search_results: list[dict[str, Any]] = await researcher.quick_search(query)
        print(f"Search results: {len(search_results)} items")

        if search_results:
            print("✅ Search successful! Sample result:")
            first_result: dict[str, Any] = search_results[0]
            print(f"  - URL: {first_result.get('href', 'N/A')}")
            print(f"  - Content preview: {str(first_result.get('body', ''))[:100]}...")
        else:
            print("❌ No search results found")
            return False

        # Test research conductor
        print("\n=== Testing Research Conductor ===")
        research_context: list[tuple[str, str]] = await researcher.conduct_research()
        print(f"Research context: {len(research_context)} items")

        if research_context:
            print("✅ Research successful!")
            print(f"  - Context items: {len(research_context)}")
            print(f"  - Sample context: {research_context[0][:100] if research_context[0] else 'Empty'}...")
        else:
            print("❌ No research context generated")
            return False

        print("\n🎉 Full research pipeline test PASSED!")
        return True

    except Exception as e:
        print(f"❌ Research test failed: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success: bool = asyncio.run(test_research())
    sys.exit(0 if success else 1)
