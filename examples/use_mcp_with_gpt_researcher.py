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
    """Example using a local MCP server"""
    
    # Initialize GPT Researcher with MCP retriever
    researcher = GPTResearcher(
        query="Tell me about the latest advancements in AI",
        headers={
            "retriever": "mcp",
            "mcp_server_command": "python",
            "mcp_server_args": f"{os.path.join(os.path.dirname(__file__), 'mcp_server_example.py')}",
            "mcp_tool_name": "search",
            "mcp_tool_arg_max_results": "3"
        }
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
            # MCP configuration
            "mcp_server_command": "python",
            "mcp_server_args": f"{os.path.join(os.path.dirname(__file__), 'mcp_server_example.py')}",
            "mcp_tool_name": "search",
            # Tavily configuration (if you have Tavily API key)
            "tavily_api_key": os.getenv("TAVILY_API_KEY", ""),
        }
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

async def research_with_mcp_category():
    """Example using a specific MCP tool and function"""
    
    # Initialize GPT Researcher with MCP retriever using a specific category tool
    researcher = GPTResearcher(
        query="What is the science behind sleep?",
        headers={
            "retriever": "mcp",
            "mcp_server_command": "python",
            "mcp_server_args": f"{os.path.join(os.path.dirname(__file__), 'mcp_server_example.py')}",
            "mcp_tool_name": "get_category_info",
            "mcp_tool_arg_category": "health"  # Specify the category
        }
    )
    
    # Conduct research and generate report
    context = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Print the results
    print("\n\n")
    print("=" * 80)
    print("RESEARCH USING MCP WITH SPECIFIC CATEGORY")
    print("=" * 80)
    print("\nGENERATED REPORT:")
    print("-" * 40)
    print(report)
    
    return report

async def main():
    """Run all examples"""
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key: export OPENAI_API_KEY=your_key_here")
        sys.exit(1)
    
    # Run the examples
    await research_with_local_mcp()
    await research_with_multiple_retrievers()
    await research_with_mcp_category()

if __name__ == "__main__":
    asyncio.run(main()) 