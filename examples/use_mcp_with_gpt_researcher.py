#!/usr/bin/env python
"""
Example of using MCP with GPT Researcher programmatically

This script demonstrates how to use the GPT Researcher with MCP servers
programmatically.

Before running this script:
1. Install GPT Researcher: `pip install gpt-researcher`
2. Install MCP SDK: `pip install mcp`
3. Set your OpenAI API key: `export OPENAI_API_KEY=your_key_here`
"""

import asyncio
import os
import sys
from typing import Dict, Any, List

from gpt_researcher import GPTResearcher

async def research_with_local_mcp():
    """Example using a local MCP server via mcp_configs"""
    
    # Initialize GPT Researcher with MCP retriever using mcp_configs
    researcher = GPTResearcher(
        query="Tell me about the latest advancements in AI",
        mcp_configs=[
            {
                "server_command": "python",
                "server_args": [os.path.join(os.path.dirname(__file__), 'mcp_server_example.py')],
                "tool_name": "search",
                "tool_args": {
                    "max_results": "3"
                }
            }
        ]
    )
    
    # Conduct research and generate report
    context = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Print the results
    print("=" * 80)
    print("RESEARCH USING LOCAL MCP SERVER")
    print("=" * 80)
    print("\nGENERATED REPORT:")
    print("-" * 40)
    print(report)
    
    return report

async def research_with_multiple_retrievers():
    """Example using both MCP and Tavily retrievers"""
    
    # Initialize GPT Researcher with multiple retrievers
    researcher = GPTResearcher(
        query="Explain the impacts of climate change",
        headers={
            "retrievers": "mcp,tavily",  # Use both MCP and Tavily
            # Tavily configuration (if you have Tavily API key)
            "tavily_api_key": os.getenv("TAVILY_API_KEY", ""),
        },
        mcp_configs=[
            {
                "server_command": "python",
                "server_args": [os.path.join(os.path.dirname(__file__), 'mcp_server_example.py')],
                "tool_name": "search"
            }
        ]
    )
    
    # Conduct research and generate report
    context = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Print the results
    print("\n\n")
    print("=" * 80)
    print("RESEARCH USING MULTIPLE RETRIEVERS (MCP + TAVILY)")
    print("=" * 80)
    print("\nGENERATED REPORT:")
    print("-" * 40)
    print(report)
    
    return report

async def research_with_multiple_mcp_servers():
    """Example using multiple MCP servers at once"""
    
    # Initialize GPT Researcher with multiple MCP servers
    researcher = GPTResearcher(
        query="What is the science behind sleep?",
        mcp_configs=[
            # First MCP server - for general search
            {
                "server_command": "python",
                "server_args": [os.path.join(os.path.dirname(__file__), 'mcp_server_example.py')],
                "tool_name": "search",
                "tool_args": {
                    "domain": "general"
                }
            },
            # Second MCP server - for health-specific data
            {
                "server_command": "python",
                "server_args": [os.path.join(os.path.dirname(__file__), 'mcp_health_server_example.py')],
                "tool_name": "get_health_info",
                "tool_args": {
                    "topic": "sleep"
                },
                "env": {
                    "HEALTH_API_KEY": os.getenv("HEALTH_API_KEY", "")
                }
            }
        ]
    )
    
    # Conduct research and generate report
    context = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Print the results
    print("\n\n")
    print("=" * 80)
    print("RESEARCH USING MULTIPLE MCP SERVERS")
    print("=" * 80)
    print("\nGENERATED REPORT:")
    print("-" * 40)
    print(report)
    
    return report

async def research_with_github_mcp():
    """Example using the GitHub MCP server"""
    
    # Initialize GPT Researcher with GitHub MCP server
    researcher = GPTResearcher(
        query="How does React Hooks work?",
        mcp_configs=[
            {
                "server_command": "npx",
                "server_args": ["-y", "@modelcontextprotocol/server-github"],
                "tool_name": "searchCode",
                "tool_args": {
                    "query": "useState in:file language:javascript",
                    "maxResults": "5"
                },
                "env": {
                    "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "")
                }
            }
        ]
    )
    
    # Conduct research and generate report
    context = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Print the results
    print("\n\n")
    print("=" * 80)
    print("RESEARCH USING GITHUB MCP SERVER")
    print("=" * 80)
    print("\nGENERATED REPORT:")
    print("-" * 40)
    print(report)
    
    return report

async def research_with_remote_mcp():
    """Example using a remote MCP server with auto-detected connection type"""
    
    # Initialize GPT Researcher with a remote MCP server
    # Note: No connection_type needed as it's auto-detected from the URL
    researcher = GPTResearcher(
        query="What are the latest climate change statistics?",
        mcp_configs=[
            {
                # URL with wss:// prefix automatically sets connection_type to "websocket"
                "connection_url": "wss://example-mcp-server.com/ws",
                "connection_token": "your_auth_token",
                "tool_name": "search_climate_data"
            }
        ]
    )
    
    # For demonstration purposes only - would fail without a real server
    try:
        print("\n\n")
        print("=" * 80)
        print("RESEARCH USING REMOTE MCP SERVER (CONNECTION TYPE AUTO-DETECTION)")
        print("=" * 80)
        
        # This will attempt to connect but will fail with the fictional server URL
        context = await researcher.conduct_research()
        report = await researcher.write_report()
        
        print("\nGENERATED REPORT:")
        print("-" * 40)
        print(report)
        
        return report
    except Exception as e:
        print(f"Expected error with remote MCP server: {e}")
        print("Note: This example requires a real remote MCP server to work.")
        print("The connection fails as expected since we're using a fictional URL.")
        return "Remote MCP example (failed as expected)"

async def main():
    """Run all examples"""
    print("Running MCP examples for GPT Researcher...")
    
    try:
        await research_with_local_mcp()
        await research_with_multiple_retrievers()
        await research_with_multiple_mcp_servers()
        
        # Demonstrate remote server connection with auto-detection
        # Note: This won't actually run the research since the server URL is fictitious
        await research_with_remote_mcp()
        
        # Only run GitHub example if token is available
        if os.getenv("GITHUB_TOKEN"):
            await research_with_github_mcp()
        else:
            print("\nSkipping GitHub MCP example - GITHUB_TOKEN not found")
            
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 