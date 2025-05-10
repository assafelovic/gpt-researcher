"""
Example MCP Server for GPT Researcher

This is a simple MCP server implementation that demonstrates how to create
a custom data source for GPT Researcher.

To use this server, run:
    python example_server.py

Then configure GPT Researcher to use it:
    RETRIEVER=mcp
    MCP_SERVER_COMMAND=python
    MCP_SERVER_ARGS=path/to/example_server.py
    MCP_TOOL_NAME=search
"""

import asyncio
from mcp.server.fastmcp import FastMCP, ToolParameter

# Create an MCP server
mcp_server = FastMCP("ExampleServer", description="Example MCP server for GPT Researcher")

# Sample data to search through
research_data = [
    {
        "title": "Introduction to MCP",
        "content": """
        The Model Context Protocol (MCP) is an open standard for connecting AI systems with data sources and tools.
        It provides a unified protocol for accessing contextual information, executing commands, and using predefined templates.
        MCP solves the "N times M problem" where numerous AI applications need to access various data sources and tools.
        """
    },
    {
        "title": "Using MCP with GPT Researcher",
        "content": """
        GPT Researcher supports MCP as a retrieval source, allowing it to use any MCP-compatible server
        as a data source for research. This enables GPT Researcher to access specialized knowledge bases,
        private data stores, and custom tools through a standard interface.
        """
    },
    {
        "title": "Creating Custom MCP Servers",
        "content": """
        You can create custom MCP servers to integrate with GPT Researcher using the MCP SDK.
        This example demonstrates a simple search server, but you can create more complex servers
        that access databases, APIs, or other data sources.
        """
    }
]

@mcp_server.tool(
    parameters=[
        ToolParameter("query", "string", "The search query"),
        ToolParameter("max_results", "integer", "Maximum number of results to return", default=10)
    ]
)
async def search(query: str, max_results: int = 10) -> list:
    """
    Search for information based on the query.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        A list of search results
    """
    # Simple keyword search implementation
    results = []
    for item in research_data:
        if query.lower() in item["title"].lower() or query.lower() in item["content"].lower():
            results.append({
                "title": item["title"],
                "body": item["content"],
                "href": f"example://document/{item['title'].replace(' ', '-').lower()}"
            })
    
    # Sort by relevance (simple implementation just checks if query is in title)
    results.sort(key=lambda x: query.lower() in x["title"].lower(), reverse=True)
    
    return results[:max_results]

@mcp_server.tool()
async def list_documents() -> list:
    """List all available documents"""
    return [{"title": item["title"]} for item in research_data]

@mcp_server.resource("example-resource")
async def get_example_resource() -> tuple[str, str]:
    """Return an example resource"""
    content = """
    # Example MCP Resource
    
    This is an example resource that can be accessed via MCP.
    Resources in MCP are static content that can be accessed by name.
    
    Unlike tools, resources don't accept parameters and always return the same content.
    """
    return content, "text/markdown"

# Run the server
if __name__ == "__main__":
    mcp_server.run() 