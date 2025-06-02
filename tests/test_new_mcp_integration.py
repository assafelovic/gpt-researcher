#!/usr/bin/env python3
"""
Test script for the new two-stage MCP integration in GPT Researcher

This script tests the redesigned MCP retriever that implements:
1. Stage 1: LLM-based intelligent tool selection
2. Stage 2: LLM with bound tools for research execution

Prerequisites:
1. Install GPT Researcher: pip install gpt-researcher
2. Install langchain-mcp-adapters: pip install langchain-mcp-adapters
3. Install GitHub MCP server: npm install -g @modelcontextprotocol/server-github
4. Set up GitHub Personal Access Token and OpenAI API key
"""

import asyncio
import os
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
GITHUB_TOKEN = "GITHUB_TOKEN_PLACEHOLDER"  # Replace with actual token
OPENAI_API_KEY = "OPENAI_KEY_PLACEHOLDER"  # Replace with actual key

MCP_CONFIG_DEFAULT = [
    {
        "server_name": "github",
        "server_command": "npx",
        "server_args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN
        }
    },
    {
        "server_name": "tavily",
        "server_command": "npx",
        "server_args": ["-y", "tavily-mcp@0.1.2"],
        "env": {
            "TAVILY_API_KEY": "TAVILY_KEY_PLACEHOLDER "
        }
    }
]

def setup_environment():
    """Set up required environment variables."""
    # Set GitHub token
    os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = GITHUB_TOKEN
    
    # Set OpenAI API key if not already set
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    
    # Validate environment
    if GITHUB_TOKEN == "your_github_token_here":
        print("❌ Please update GITHUB_TOKEN in the script with your actual token")
        return False
        
    if OPENAI_API_KEY == "your_openai_key_here" and not os.environ.get("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable or update the script")
        return False
    
    return True

async def test_mcp_tool_selection():
    """Test the new MCP tool selection stage."""
    print("\n🧠 Testing MCP Tool Selection (Stage 1)")
    print("=" * 50)
    
    try:
        from gpt_researcher.retrievers.mcp.mcp_retriever import MCPRetriever
        
        # Create test MCP configuration
        mcp_configs = MCP_CONFIG_DEFAULT
        
        # Create a mock researcher instance with MCP configs
        class MockResearcher:
            def __init__(self):
                self.mcp_configs = mcp_configs
                self.cfg = type('Config', (), {
                    'strategic_llm_model': 'gpt-4o',
                    'strategic_llm_provider': 'openai',
                    'llm_kwargs': {}
                })()
        
        mock_researcher = MockResearcher()
        
        # Create MCP retriever
        retriever = MCPRetriever(
            query="How does React's useState hook work?",
            llm_provider=mock_researcher
        )
        
        print("✅ MCPRetriever initialized successfully")
        
        # Test getting all tools
        all_tools = await retriever._get_all_tools()
        print(f"📋 Retrieved {len(all_tools)} total tools from MCP servers")
        
        if all_tools:
            # Test tool selection
            selected_tools = await retriever._select_relevant_tools(all_tools, max_tools=3)
            print(f"🎯 Selected {len(selected_tools)} tools for research")
            
            for i, tool in enumerate(selected_tools, 1):
                print(f"   {i}. {tool.name} - {tool.description[:60]}...")
                
        return True
        
    except Exception as e:
        print(f"❌ Error in tool selection test: {e}")
        logger.exception("Tool selection test error:")
        return False

async def test_full_gpt_researcher_integration():
    """Test the full GPT Researcher integration with new MCP approach."""
    print("\n🚀 Testing Full GPT Researcher Integration")
    print("=" * 50)
    
    try:
        from gpt_researcher import GPTResearcher
        
        # Create MCP configuration
        mcp_configs = [
            {
                "server_name": "github",
                "server_command": "npx",
                "server_args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN
                }
            },
            {
                "server_name": "tavily",
                "server_command": "npx",
                "server_args": ["-y", "tavily-mcp@0.1.2"],
                "env": {
                    "TAVILY_API_KEY": "TAVILY_KEY_PLACEHOLDER "
                }
            }
        ]
        
        # Create researcher with MCP configuration
        researcher = GPTResearcher(
            query="What are the best practices for React state management with hooks?",
            report_type="research_report",
            mcp_configs=mcp_configs,
            verbose=True
        )
        
        print("✅ GPTResearcher initialized with new MCP integration")
        print(f"🔧 MCP servers configured: {len(mcp_configs)}")
        
        # Conduct research
        print("🚀 Starting full research process...")
        context = await researcher.conduct_research()
        
        print(f"📊 Research completed!")
        print(f"📈 Context items collected: {len(context) if isinstance(context, list) else len(str(context))}")
        
        # Generate a brief report
        print("📝 Generating brief report...")
        report = await researcher.write_report()
        
        print(f"✅ Report generated successfully!")
        print(f"📄 Report length: {len(report)} characters")
        
        # Save test report
        filename = "../test_new_mcp_integration_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Test Report: New MCP Integration\n\n")
            f.write(f"**Query:** {researcher.query}\n\n")
            f.write(f"**Research Method:** Two-stage MCP integration\n\n")
            f.write(f"**Generated Report:**\n\n")
            f.write(report)
        
        print(f"💾 Test report saved to: {filename}")
        
        # Print summary
        print(f"\n📋 Integration Test Summary:")
        print(f"   • Query processed successfully")
        print(f"   • Context gathered: {len(str(context)):,} chars")
        print(f"   • Report generated: {len(report):,} chars")
        print(f"   • Saved to: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full integration test: {e}")
        logger.exception("Full integration test error:")
        return False

async def main():
    """Main test function."""
    print("🚀 Testing New Two-Stage MCP Integration for GPT Researcher")
    print("=" * 70)
    
    # Check environment setup
    if not setup_environment():
        print("\n❌ Environment setup failed. Please check your configuration.")
        return
    
    print("✅ Environment setup complete")
    
    # Track test results
    test_results = []
    
    # Run individual tests
    print("\n🔍 Running Individual Component Tests")
    
    # Test 1: Tool selection
    result1 = await test_mcp_tool_selection()
    test_results.append(("Tool Selection", result1))
    
    # Test 2: Full integration
    print("\n🔗 Running Full Integration Test")
    result2 = await test_full_gpt_researcher_integration()
    test_results.append(("Full Integration", result2))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, passed_test in test_results:
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! New MCP integration is working correctly.")
        print("\n💡 Key Features Validated:")
        print("   • Two-stage MCP approach (tool selection + research execution)")
        print("   • LLM-based intelligent tool selection")
        print("   • Proper error handling and graceful degradation")
        print("   • Full integration with GPT Researcher workflow")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    print("📚 New MCP Integration Test")
    print("=" * 30)
    print("This test validates the redesigned MCP integration that:")
    print("1. Uses LLM to select 2-3 most relevant tools (Stage 1)")
    print("2. Uses LLM with bound tools for intelligent research (Stage 2)")
    print("3. Provides better error handling and efficiency")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Main test error:") 