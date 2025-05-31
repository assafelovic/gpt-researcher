#!/usr/bin/env python3
"""
Test script for the GPT Researcher MCP server.
"""

import os
import asyncio
import subprocess
import time
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_mcp_server():
    """Test the MCP server by conducting a simple research task."""
    print("Starting MCP server test...")
    
    # Start the server process
    server_process = subprocess.Popen(
        ["python", "../server.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Give the server time to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["../server.py"],
        env=dict(os.environ),
    )
    
    try:
        # Connect to the server
        print("Connecting to server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                print("Connected to server")
                
                # List available tools
                tools = await session.list_tools()
                print(f"Available tools: {[tool.name for tool in tools]}")
                
                # List available prompts
                prompts = await session.list_prompts()
                print(f"Available prompts: {[prompt.name for prompt in prompts]}")
                
                # Call conduct_research tool
                print("Conducting research...")
                research_result = await session.call_tool(
                    "conduct_research",
                    arguments={
                        "query": "What are the latest advancements in renewable energy?",
                        "report_type": "outline_report"
                    }
                )
                print(f"Research result: {research_result}")
                
                if "research_id" in research_result:
                    research_id = research_result["research_id"]
                    
                    # Call write_report tool
                    print("Generating report...")
                    report_result = await session.call_tool(
                        "write_report",
                        arguments={"research_id": research_id}
                    )
                    print(f"Report status: {report_result['status']}")
                    
                    # Call get_research_sources tool
                    print("Getting sources...")
                    sources_result = await session.call_tool(
                        "get_research_sources",
                        arguments={"research_id": research_id}
                    )
                    print(f"Source count: {len(sources_result.get('sources', []))}")
                
                print("Test completed successfully!")
    
    except Exception as e:
        print(f"Error during test: {str(e)}")
    
    finally:
        # Terminate the server process
        server_process.terminate()
        server_process.wait()
        print("Server terminated")


if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 