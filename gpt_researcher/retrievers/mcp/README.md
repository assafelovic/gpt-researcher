# MCP Retriever for GPT Researcher

This module provides integration between GPT Researcher and [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers.

## What is MCP?

The Model Context Protocol (MCP) is an open standard for connecting AI systems with data sources and tools. It provides a unified protocol for:

- Accessing contextual information (resources)
- Executing commands (tools)
- Using predefined templates (prompts)

MCP solves the "N times M problem" where numerous AI applications need to access various data sources and tools.

## Installation

The MCP retriever requires the `mcp` Python package. It's listed as an optional dependency in the requirements.txt file:

```bash
pip install "mcp>=1.0.0"
```

## Usage

### Basic Configuration

To use an MCP server as a data source, set `RETRIEVER=mcp` in your environment variables or specify it when creating a GPT Researcher instance:

```python
researcher = GPTResearcher(
    query="your query",
    report_type="research_report",
    retriever="mcp",
    # MCP-specific configuration can be passed via headers
    headers={
        "mcp_server_command": "python",
        "mcp_server_args": "-m my_mcp_server",
        # ... other MCP configuration
    }
)
```

### Connection Types

The MCP Retriever supports three types of connections:

1. **Stdio** (default): Spawns a local MCP server process and communicates via standard input/output
2. **WebSocket**: Connects to a remote MCP server via WebSocket
3. **HTTP**: Connects to a remote MCP server via HTTP

#### Local MCP Server (Stdio)

```python
researcher = GPTResearcher(
    query="your query",
    headers={
        "retriever": "mcp",
        "mcp_connection_type": "stdio",  # This is the default
        "mcp_server_command": "python",
        "mcp_server_args": "-m my_mcp_server",
        "mcp_tool_name": "search"
    }
)
```

#### Remote MCP Server (WebSocket)

```python
researcher = GPTResearcher(
    query="your query",
    headers={
        "retriever": "mcp",
        "mcp_connection_type": "websocket",
        "mcp_connection_url": "wss://my-mcp-server.example.com/ws",
        "mcp_connection_token": "your_auth_token",  # Optional
        "mcp_tool_name": "search"
    }
)
```

#### Remote MCP Server (HTTP)

```python
researcher = GPTResearcher(
    query="your query",
    headers={
        "retriever": "mcp",
        "mcp_connection_type": "http",
        "mcp_connection_url": "https://my-mcp-server.example.com/api",
        "mcp_connection_token": "your_auth_token",  # Optional
        "mcp_tool_name": "search"
    }
)
```

### Configuration Options

The MCP Retriever accepts the following configuration parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `mcp_server_name` | Name of the MCP server | `"github"` |
| `mcp_server_command` | Command to start the MCP server | `"python"` |
| `mcp_server_args` | Arguments for the server command | `"-m my_mcp_server"` |
| `mcp_resource_uri` | URI template for accessing a resource | `"file://{query}"` |
| `mcp_tool_name` | Name of the MCP tool to invoke | `"search"` |
| `mcp_tool_arg_*` | Arguments for the tool (prefix with `mcp_tool_arg_`) | `"mcp_tool_arg_query=..."` |
| `mcp_env_*` | Environment variables (prefix with `mcp_env_`) | `"mcp_env_API_KEY=..."` |
| `mcp_connection_type` | Type of connection: stdio, websocket, or http | `"websocket"` |
| `mcp_connection_url` | URL for WebSocket or HTTP connection | `"wss://example.com/ws"` |
| `mcp_connection_token` | Authentication token for remote connections | `"your_auth_token"` |

### Example: Using GitHub MCP Server

```python
from gpt_researcher import GPTResearcher

researcher = GPTResearcher(
    query="How does React.js useState hook work?",
    headers={
        "retriever": "mcp",
        "mcp_server_command": "npx",
        "mcp_server_args": "-y @modelcontextprotocol/server-github",
        "mcp_env_GITHUB_TOKEN": "your_github_token",
        "mcp_tool_name": "searchCode",
        "mcp_tool_arg_query": "useState in:file language:javascript",
        "mcp_tool_arg_maxResults": "5"
    }
)

context = await researcher.conduct_research()
report = await researcher.write_report()
print(report)
```

### Example: Using a Cloud-Hosted MCP Server

```python
from gpt_researcher import GPTResearcher

researcher = GPTResearcher(
    query="Analyze recent cybersecurity threats",
    headers={
        "retriever": "mcp",
        "mcp_connection_type": "websocket",
        "mcp_connection_url": "wss://api.cybersecurity-mcp.example.com/ws",
        "mcp_connection_token": "your_api_key",
        "mcp_tool_name": "searchThreats",
        "mcp_tool_arg_timeframe": "30d",
        "mcp_tool_arg_severity": "high"
    }
)

context = await researcher.conduct_research()
report = await researcher.write_report()
print(report)
```

### Using Multiple Retrievers

You can use MCP alongside other retrievers:

```python
researcher = GPTResearcher(
    query="How does React.js useState hook work?",
    headers={
        "retrievers": "mcp,tavily",  # Use both MCP and Tavily
        # MCP configuration
        "mcp_server_command": "...",
        # ... other config
    }
)
```

## Available MCP Servers

You can use any MCP-compatible server with this retriever. Some popular options include:

- **GitHub**: Code searching and repository management
- **Filesystem**: Access to local files and directories
- **Google Drive**: File storage and search
- **PostgreSQL**: Database access
- **Memory**: Knowledge graph persistence
- **Tavily Search**: Web search capabilities

For a comprehensive list, check the [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) repository, which includes hundreds of MCP server implementations for various services and data sources.

## Creating Custom MCP Servers

You can create your own MCP servers to integrate with GPT Researcher using the MCP SDK:

```python
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("MyCustomServer")

# Add a search tool
@mcp.tool()
def search(query: str, max_results: int = 10) -> list:
    """Search for information based on the query"""
    # Implement your custom search logic
    results = []
    # ... your search logic
    return results

# Run the server
if __name__ == "__main__":
    mcp.run()
```

Then use it with GPT Researcher:

```python
researcher = GPTResearcher(
    query="your query",
    headers={
        "retriever": "mcp",
        "mcp_server_command": "python",
        "mcp_server_args": "path/to/your_server.py",
        "mcp_tool_name": "search"
    }
)
```

## Hosting Your Own MCP Server

You can host your MCP server remotely and use it with GPT Researcher:

1. Deploy your MCP server to a cloud provider (e.g., AWS, Google Cloud, Vercel)
2. Set up WebSocket or HTTP endpoints for the server
3. Configure the MCP Retriever to connect to your remote server:

```python
researcher = GPTResearcher(
    query="your query",
    headers={
        "retriever": "mcp",
        "mcp_connection_type": "websocket",  # or "http"
        "mcp_connection_url": "wss://your-deployed-mcp-server.com/ws",
        "mcp_connection_token": "your_secret_token",  # For authentication
        "mcp_tool_name": "search"
    }
)
```

## References

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Example Servers](https://modelcontextprotocol.io/examples)
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) 