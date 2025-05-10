#!/usr/bin/env python
"""
Example of using Tavily MCP with GPT Researcher

This script demonstrates how to use Tavily Search via MCP with GPT Researcher.
Tavily provides high-quality search results and is recommended as a web search
retriever for GPT Researcher.

Before running this script:
1. Install GPT Researcher: `pip install gpt-researcher`
2. Install MCP SDK: `pip install mcp`
3. Get a Tavily API key from https://tavily.com
4. Set your API keys:
   export OPENAI_API_KEY=your_openai_key_here
   export TAVILY_API_KEY=your_tavily_key_here
"""

import asyncio
import os
import sys
from typing import Dict, Any, List

from gpt_researcher import GPTResearcher

async def research_with_tavily_mcp():
    """Example using Tavily Search MCP server"""
    
    # Check if Tavily API key is set
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        print("Error: TAVILY_API_KEY environment variable not set.")
        print("Please get an API key from https://tavily.com and set it.")
        return None
    
    # Initialize GPT Researcher with Tavily MCP retriever
    researcher = GPTResearcher(
        query="What are the latest advancements in renewable energy?",
        headers={
            "retriever": "mcp",
            "mcp_server_command": "npx",
            "mcp_server_args": "-y tavily-mcp",
            "mcp_env_TAVILY_API_KEY": tavily_api_key,
            "mcp_tool_name": "search",
            "mcp_tool_arg_max_results": "5",
            "mcp_tool_arg_search_depth": "advanced"  # Can be 'basic' or 'advanced'
        }
    )
    
    # Conduct research and generate report
    print("Conducting research using Tavily MCP...")
    context = await researcher.conduct_research()
    
    print("Generating report...")
    report = await researcher.write_report()
    
    # Print the results
    print("\n" + "=" * 80)
    print("RESEARCH REPORT USING TAVILY MCP")
    print("=" * 80)
    print("\n" + report)
    
    return report

async def main():
    """Run the example"""
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key: export OPENAI_API_KEY=your_key_here")
        sys.exit(1)
    
    # Run the Tavily MCP example
    await research_with_tavily_mcp()

if __name__ == "__main__":
    asyncio.run(main()) 