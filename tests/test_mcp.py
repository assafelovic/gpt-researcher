#!/usr/bin/env python3
"""
Test script for MCP integration in GPT Researcher

This script tests two MCP integration scenarios:
1. Web Search MCP (Tavily) - News and general web search queries
2. GitHub MCP - Code repository and technical documentation queries

Both tests verify:
- MCP server connection and tool usage
- Research execution with default optimal settings
- Report generation with MCP data

Prerequisites:
1. Install GPT Researcher: pip install gpt-researcher
2. Install MCP servers:
   - Web Search: npm install -g tavily-mcp
   - GitHub: npm install -g @modelcontextprotocol/server-github
3. Set up environment variables:
   - GITHUB_PERSONAL_ACCESS_TOKEN: Your GitHub Personal Access Token
   - OPENAI_API_KEY: Your OpenAI API key
   - TAVILY_API_KEY: Your Tavily API key
"""

import asyncio
import os
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API keys from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# Test configuration using environment variables
def get_mcp_config():
    """Get MCP configuration with environment variables."""
    return [
        {
            "name": "tavily",
            "command": "npx",
            "args": ["-y", "tavily-mcp@0.1.2"],
            "env": {
                "TAVILY_API_KEY": TAVILY_API_KEY
            }
        }
    ]

def get_github_mcp_config():
    """Get GitHub MCP configuration with environment variables."""
    return [
        {
            "name": "github",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN
            }
        }
    ]

def setup_environment():
    """Validate required environment variables."""
    required_vars = {
        "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "TAVILY_API_KEY": TAVILY_API_KEY
    }
    
    missing_vars = []
    
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\nPlease set these environment variables before running the test:")
        print("   export GITHUB_PERSONAL_ACCESS_TOKEN='your_github_token'")
        print("   export OPENAI_API_KEY='your_openai_key'")
        print("   export TAVILY_API_KEY='your_tavily_key'")
        return False
    
    print("✅ All required environment variables are set")
    return True

async def test_web_search_mcp():
    """Test MCP integration with web search (Tavily) for news and general topics."""
    print("\n🌐 Testing Web Search MCP Integration")
    print("=" * 50)
    
    try:
        from gpt_researcher import GPTResearcher
        
        # Create web search MCP configuration
        mcp_configs = get_mcp_config()
        
        # Create researcher with web search query
        query = "What is the latest updates in the NBA playoffs?"
        researcher = GPTResearcher(
            query=query,
            mcp_configs=mcp_configs
        )
        
        print("✅ GPTResearcher initialized with web search MCP")
        print(f"🔧 MCP servers configured: {len(mcp_configs)} (Tavily)")
        print(f"📝 Query: {query}")
        
        # Conduct research - should use fast strategy by default
        print("🚀 Starting web search research...")
        context = await researcher.conduct_research()
        
        print(f"📊 Web search research completed!")
        print(f"📈 Context collected: {len(str(context)) if context else 0} chars")
        
        # Generate a brief report
        print("📝 Generating report...")
        report = await researcher.write_report()
        
        print(f"✅ Report generated successfully!")
        print(f"📄 Report length: {len(report)} characters")
        
        # Save test report
        filename = "../test_web_search_mcp_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Test Report: Web Search MCP Integration\n\n")
            f.write(f"**Query:** {researcher.query}\n\n")
            f.write(f"**MCP Server:** Tavily (Web Search)\n\n")
            f.write(f"**Generated Report:**\n\n")
            f.write(report)
        
        print(f"💾 Test report saved to: {filename}")
        
        # Print summary
        print(f"\n📋 Web Search MCP Test Summary:")
        print(f"   • News query processed successfully")
        print(f"   • Context gathered: {len(str(context)):,} chars")
        print(f"   • Report generated: {len(report):,} chars")
        print(f"   • Cost: ${researcher.get_costs():.4f}")
        print(f"   • Saved to: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in web search MCP test: {e}")
        logger.exception("Web search MCP test error:")
        return False

async def test_github_mcp():
    """Test MCP integration with GitHub for code-related queries."""
    print("\n🐙 Testing GitHub MCP Integration")
    print("=" * 50)
    
    try:
        from gpt_researcher import GPTResearcher
        
        # Create GitHub MCP configuration
        mcp_configs = get_github_mcp_config()
        
        # Create researcher with code-related query
        query = "What are the key features and implementation of React's useState hook? How has it evolved in recent versions?"
        researcher = GPTResearcher(
            query=query,
            mcp_configs=mcp_configs
        )
        
        print("✅ GPTResearcher initialized with GitHub MCP")
        print(f"🔧 MCP servers configured: {len(mcp_configs)} (GitHub)")
        print(f"📝 Query: {query}")
        
        # Conduct research - should use fast strategy by default
        print("🚀 Starting GitHub code research...")
        context = await researcher.conduct_research()
        
        print(f"📊 GitHub research completed!")
        print(f"📈 Context collected: {len(str(context)) if context else 0} chars")
        
        # Generate a brief report
        print("📝 Generating report...")
        report = await researcher.write_report()
        
        print(f"✅ Report generated successfully!")
        print(f"📄 Report length: {len(report)} characters")
        
        # Save test report
        filename = "../test_github_mcp_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Test Report: GitHub MCP Integration\n\n")
            f.write(f"**Query:** {researcher.query}\n\n")
            f.write(f"**MCP Server:** GitHub (Code Repository)\n\n")
            f.write(f"**Generated Report:**\n\n")
            f.write(report)
        
        print(f"💾 Test report saved to: {filename}")
        
        # Print summary
        print(f"\n📋 GitHub MCP Test Summary:")
        print(f"   • Code query processed successfully")
        print(f"   • Context gathered: {len(str(context)):,} chars")
        print(f"   • Report generated: {len(report):,} chars")
        print(f"   • Cost: ${researcher.get_costs():.4f}")
        print(f"   • Saved to: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in GitHub MCP test: {e}")
        logger.exception("GitHub MCP test error:")
        return False

async def main():
    """Main test function."""
    print("🚀 Testing MCP Integration with GPT Researcher")
    print("=" * 50)
    
    # Check environment setup
    if not setup_environment():
        print("\n❌ Environment setup failed. Please check your configuration.")
        return
    
    print("✅ Environment setup complete")
    
    # Track test results
    test_results = []
    
    # Run Web Search MCP test
    print("\n🌐 Running Web Search MCP Test (Tavily)")
    result1 = await test_web_search_mcp()
    test_results.append(("Web Search MCP", result1))
    
    # Run GitHub MCP test
    print("\n🐙 Running GitHub MCP Test")
    result2 = await test_github_mcp()
    test_results.append(("GitHub MCP", result2))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, passed_test in test_results:
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All MCP integration tests completed successfully!")
        print("⚡ Both Web Search (news) and GitHub (code) MCP servers work seamlessly!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    print("🔧 MCP Integration Tests")
    print("=" * 30)
    print("Testing Web Search (Tavily) and GitHub MCP integrations with optimal default settings.")
    print()
    
    asyncio.run(main()) 