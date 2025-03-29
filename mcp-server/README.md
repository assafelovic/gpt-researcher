# GPT Researcher MCP Server

This directory contains the MCP (Machine Conversation Protocol) server implementation for GPT Researcher, allowing AI assistants to conduct web research and generate reports via the MCP protocol.

## Files Structure

- `server.py` - Main MCP server implementation with endpoint decorators
- `utils.py` - Utility functions and helpers for the server

## Architecture

The code has been organized into a modular structure:

1. **server.py**: Contains the core MCP server configuration and endpoint handlers with decorators:
   - `@mcp.resource("research://{topic}")` - Research resource endpoint
   - `@mcp.tool()` - Tool endpoints for research operations
   - `@mcp.prompt()` - Prompt template for research queries
   - Server initialization and running logic

2. **utils.py**: Contains utility functions and helpers:
   - Response formatting utilities
   - Research store management
   - Source formatting helpers
   - Exception handling
   - Research prompt generation

## Features

- Web research capabilities through GPT Researcher
- MCP protocol support for AI assistants
- Research report generation in different formats
- Access to research sources, context, costs, and images

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/researcher-mcp-server.git
cd researcher-mcp-server
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

## Usage

To run the MCP server:

```bash
python server.py
```

Make sure you have set up the required environment variables in a `.env` file, including:

- `OPENAI_API_KEY` - Your OpenAI API key for accessing language models

## Dependencies

- `mcp` - Machine Conversation Protocol library
- `gpt_researcher` - Core GPT Researcher functionality
- `dotenv` - Environment variable management
- `loguru` - Logging utilities

## Design Decisions

- **Modularity**: Functions are separated by responsibility to make the code more maintainable
- **Error Handling**: Consistent error handling pattern across all endpoints
- **Response Formatting**: Standardized response formats for API consistency
- **Data Storage**: In-memory storage for research results and session management

## Examples

### Example usage with Claude:

```
I want to research the latest advancements in quantum computing. Please use the conduct_research tool to find information, then write a report summarizing your findings.
```

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
