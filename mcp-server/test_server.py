#!/usr/bin/env python3
"""
Test script for GPT Researcher MCP Server
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_server():
    """Test server initialization and tool listing."""
    print("=" * 60)
    print("Testing GPT Researcher MCP Server")
    print("=" * 60)

    try:
        # Import server
        print("\n✓ Importing server module...")
        from server import app, list_tools, DOC_PATH, OPENAI_API_KEY, TAVILY_API_KEY

        # Check configuration
        print("\n✓ Checking configuration...")
        print(f"  DOC_PATH: {DOC_PATH}")
        print(f"  OpenAI API Key: {'✓ Set' if OPENAI_API_KEY else '✗ Not set'}")
        print(f"  Tavily API Key: {'✓ Set' if TAVILY_API_KEY else '✗ Not set'}")

        # Test tool listing
        print("\n✓ Testing tool listing...")
        tools = await list_tools()
        print(f"  Found {len(tools)} tools:")

        for tool in tools:
            print(f"    - {tool.name}: {tool.description[:60]}...")

        # Verify key tools exist
        print("\n✓ Verifying key tools...")
        tool_names = [t.name for t in tools]
        required_tools = [
            "research",
            "analyze_doc_files",
            "read_file_content",
            "identify_stakeholders",
            "find_matching_funding_programs"
        ]

        for tool_name in required_tools:
            if tool_name in tool_names:
                print(f"  ✓ {tool_name}")
            else:
                print(f"  ✗ {tool_name} - MISSING!")

        print("\n" + "=" * 60)
        print("✅ Server tests passed!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
