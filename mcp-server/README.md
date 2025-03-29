# GPT Researcher MCP Server

This server provides Model Context Protocol (MCP) integration for GPT Researcher, allowing AI assistants to perform web research and generate reports via the MCP protocol.

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

### Starting the server

To start the MCP server:

```bash
python server.py
```

Or using the MCP CLI:

```bash
mcp run server.py
```

### Using with Claude or other MCP clients

The server exposes the following capabilities:

#### Tools

- `conduct_research`: Conduct web research on a topic
- `write_report`: Generate a report based on research results
- `get_research_sources`: Get the sources used in the research
- `get_research_context`: Get the full context of the research

#### Prompts

- `research_query`: Create a research query prompt

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
