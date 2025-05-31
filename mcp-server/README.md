# 🔍 GPT Researcher MCP Server

> **Note:** This content has been moved to a dedicated repository: [https://github.com/assafelovic/gptr-mcp](https://github.com/assafelovic/gptr-mcp)

## Overview

The GPT Researcher MCP Server enables AI assistants like Claude to conduct comprehensive web research and generate detailed reports via the Machine Conversation Protocol (MCP).

## Why GPT Researcher MCP?

While LLM apps can access web search tools with MCP, **GPT Researcher MCP delivers deep research results.** Standard search tools return raw results requiring manual filtering, often containing irrelevant sources and wasting context window space.

GPT Researcher autonomously explores and validates numerous sources, focusing only on relevant, trusted and up-to-date information. Though slightly slower than standard search (~30 seconds wait), it delivers:

* ✨ Higher quality information
* 📊 Optimized context usage
* 🔎 Comprehensive results
* 🧠 Better reasoning for LLMs

## Features

### Resources
* `research_resource`: Get web resources related to a given task via research.

### Primary Tools
* `deep_research`: Performs deep web research on a topic, finding reliable and relevant information
* `quick_search`: Performs a fast web search optimized for speed over quality 
* `write_report`: Generate a report based on research results
* `get_research_sources`: Get the sources used in the research
* `get_research_context`: Get the full context of the research

## Installation

For detailed installation and usage instructions, please visit the [official repository](https://github.com/assafelovic/gptr-mcp).

Quick start:

1. Clone the new repository:
   ```bash
   git clone https://github.com/assafelovic/gptr-mcp.git
   cd gptr-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

4. Run the server:
   ```bash
   python server.py
   ```

For Docker deployment, Claude Desktop integration, example usage, and troubleshooting, please refer to the [full documentation](https://github.com/assafelovic/gptr-mcp).

## Support & Contact

* Website: [gptr.dev](https://gptr.dev)
* Email: assaf.elovic@gmail.com
* GitHub: [assafelovic/gptr-mcp](https://github.com/assafelovic/gptr-mcp) :-)