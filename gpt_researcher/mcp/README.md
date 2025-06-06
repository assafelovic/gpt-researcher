# GPT Researcher MCP Integration

This directory contains the comprehensive Model Context Protocol (MCP) integration for GPT Researcher. MCP enables GPT Researcher to seamlessly connect with and utilize external tools and data sources through a standardized protocol.

## 🔧 What is MCP?

Model Context Protocol (MCP) is an open standard that enables secure connections between AI applications and external data sources and tools. With MCP, GPT Researcher can:

- **Access Local Data**: Connect to databases, file systems, and local APIs
- **Use External Tools**: Integrate with web services, APIs, and third-party tools
- **Extend Capabilities**: Add custom functionality through MCP servers
- **Maintain Security**: Controlled access with proper authentication and permissions

## 📁 Module Structure

```
gpt_researcher/mcp/
├── __init__.py           # Module initialization and imports
├── client.py             # MCP client management and configuration
├── tool_selector.py      # Intelligent tool selection using LLM
├── research.py           # Research execution with selected tools
├── streaming.py          # WebSocket streaming and logging utilities
└── README.md            # This documentation
```

### Core Components

#### 🤖 `client.py` - MCPClientManager
Handles MCP server connections and client lifecycle:
- Converts GPT Researcher configs to MCP format
- Manages MultiServerMCPClient instances
- Handles connection types (stdio, websocket, HTTP)
- Provides automatic cleanup and resource management

#### 🧠 `tool_selector.py` - MCPToolSelector
Intelligent tool selection using LLM analysis:
- Analyzes available tools against research queries
- Uses strategic LLM for optimal tool selection
- Provides fallback pattern-matching selection
- Limits tool selection to prevent overhead

#### 🔍 `research.py` - MCPResearchSkill
Executes research using selected MCP tools:
- Binds tools to LLM for intelligent usage
- Manages tool execution and error handling
- Processes results into standard format
- Includes LLM analysis alongside tool results

#### 📡 `streaming.py` - MCPStreamer
Real-time streaming and logging:
- WebSocket streaming for live updates
- Structured logging for debugging
- Progress tracking and status updates
- Error and warning management

## 🚀 Getting Started

### Prerequisites

1. **Install MCP Dependencies**:
   ```bash
   pip install langchain-mcp-adapters
   ```

2. **Setup MCP Server**: You need at least one MCP server to connect to. This could be:
   - A local server you develop
   - A third-party MCP server
   - A cloud-based MCP service

### Basic Usage

#### 1. Configure MCP in GPT Researcher

```python
from gpt_researcher import GPTResearcher

# MCP configuration for a local server
mcp_configs = [{
    "command": "python",
    "args": ["my_mcp_server.py"],
    "name": "local_server",
    "tool_name": "search"  # Optional: specify specific tool
}]

# Initialize researcher with MCP
researcher = GPTResearcher(
    query="What are the latest developments in AI?",
    mcp_configs=mcp_configs
)

# Conduct research using MCP tools
context = await researcher.conduct_research()
report = await researcher.write_report()
```

#### 2. WebSocket/HTTP Server Configuration

```python
# WebSocket MCP server
mcp_configs = [{
    "connection_url": "ws://localhost:8080/mcp",
    "connection_type": "websocket",
    "name": "websocket_server"
}]

# HTTP MCP server
mcp_configs = [{
    "connection_url": "https://api.example.com/mcp",
    "connection_type": "http",
    "connection_token": "your-auth-token",
    "name": "http_server"
}]
```

#### 3. Multiple Servers

```python
mcp_configs = [
    {
        "command": "python",
        "args": ["database_server.py"],
        "name": "database",
        "env": {"DB_HOST": "localhost"}
    },
    {
        "connection_url": "ws://localhost:8080/search",
        "name": "search_service"
    },
    {
        "connection_url": "https://api.knowledge.com/mcp",
        "connection_token": "token123",
        "name": "knowledge_base"
    }
]
```

## 🔧 Configuration Options

### MCP Server Configuration

Each MCP server configuration supports the following options:

| Field              | Type | Description | Example |
|--------------------|------|-------------|---------|
| `name`             | `str` | Unique name for the server | `"my_server"` |
| `command`          | `str` | Command to start stdio server | `"python"` |
| `args`             | `list[str]` | Arguments for the command | `["server.py", "--port", "8080"]` |
| `connection_url`   | `str` | URL for websocket/HTTP connection | `"ws://localhost:8080/mcp"` |
| `connection_type`  | `str` | Connection type | `"stdio"`, `"websocket"`, `"http"` |
| `connection_token` | `str` | Authentication token | `"your-token"` |
| `tool_name`        | `str` | Specific tool to use (optional) | `"search"` |
| `env`              | `dict` | Environment variables | `{"API_KEY": "secret"}` |

### Auto-Detection Features

The MCP client automatically detects connection types:
- URLs starting with `ws://` or `wss://` → WebSocket
- URLs starting with `http://` or `https://` → HTTP  
- No URL provided → stdio (default)

## 🏗️ Development

### Adding New Components

1. **Create your component** in the appropriate file
2. **Add it to `__init__.py`** for easy importing
3. **Update this README** with documentation
4. **Add tests** in the tests directory

### Extending Tool Selection

To customize tool selection logic, extend `MCPToolSelector`:

```python
from gpt_researcher.mcp import MCPToolSelector

class CustomToolSelector(MCPToolSelector):
    def _fallback_tool_selection(self, all_tools, max_tools):
        # Custom fallback logic
        return super()._fallback_tool_selection(all_tools, max_tools)
```

### Custom Result Processing

Extend `MCPResearchSkill` for custom result processing:

```python
from gpt_researcher.mcp import MCPResearchSkill

class CustomResearchSkill(MCPResearchSkill):
    def _process_tool_result(self, tool_name, result):
        # Custom result processing
        return super()._process_tool_result(tool_name, result)
```

## 🔒 Security Considerations

- **Token Management**: Store authentication tokens securely
- **Server Validation**: Only connect to trusted MCP servers
- **Environment Variables**: Use env vars for sensitive configuration
- **Network Security**: Use HTTPS/WSS for remote connections
- **Access Control**: Implement proper permission controls

## 🐛 Troubleshooting

### Common Issues

1. **Import Error**: `langchain-mcp-adapters not installed`
   ```bash
   pip install langchain-mcp-adapters
   ```

2. **Connection Failed**: Check server URL and authentication
   - Verify server is running
   - Check connection URL format
   - Validate authentication tokens

3. **No Tools Available**: Server may not be exposing tools
   - Check server implementation
   - Verify tool registration
   - Review server logs

4. **Tool Selection Issues**: LLM may not select appropriate tools
   - Review tool descriptions
   - Check query relevance
   - Consider custom selection logic

### Debug Logging

Enable debug logging for detailed information:

```python
import logging
logging.getLogger('gpt_researcher.mcp').setLevel(logging.DEBUG)
```

## 📚 Resources

- **MCP Specification**: [Model Context Protocol Docs](https://spec.modelcontextprotocol.io/)
- **langchain-mcp-adapters**: [GitHub Repository](https://github.com/modelcontextprotocol/langchain-mcp-adapters)
- **GPT Researcher Docs**: [Documentation](https://docs.gptr.dev/)
- **Example MCP Servers**: [MCP Examples](https://github.com/modelcontextprotocol/servers)

## 🤝 Contributing

Contributions to the MCP integration are welcome! Please:

1. **Follow the project structure** outlined above
2. **Add comprehensive tests** for new functionality  
3. **Update documentation** including this README
4. **Follow coding standards** consistent with the project
5. **Consider backwards compatibility** when making changes

---

*This MCP integration brings powerful extensibility to GPT Researcher, enabling connections to virtually any data source or tool through the standardized MCP protocol.* 🙂 