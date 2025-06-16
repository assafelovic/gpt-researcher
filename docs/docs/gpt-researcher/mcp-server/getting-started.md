---
sidebar_position: 1
---

# Getting Started

The GPT Researcher MCP Server provides Model Context Protocol (MCP) integration for GPT Researcher, allowing AI assistants to perform autonomous, comprehensive web research and generate reports via the MCP protocol.

## Why GPT Researcher MCP?

While many AI apps can access web search tools with MCP, GPT Researcher MCP delivers in-depth results. Standard search tools return raw results requiring manual filtering, often containing irrelevant sources and wasting context window space.

GPT Researcher performs autonomous, deep research - not just search. It intelligently explores and validates multiple sources, focusing only on relevant and up-to-date information. Though slightly slower (30-40 seconds) than standard search, it delivers higher quality information, optimized context, comprehensive results, and better reasoning for LLMs.

The MCP server exposes the following capabilities to AI assistants:

### Resources
- `research_resource`: Get web resources related to a given task via research.

### Primary Tools

- `deep_research`: Performs autonomous web research on a topic, finding the most reliable and relevant information
- `quick_search`: Performs a fast web search optimized for speed over quality, returning search results with snippets
- `write_report`: Generate a report based on research results
- `get_research_sources`: Get the sources used in the research
- `get_research_context`: Get the full context of the research

### Prompts

- `research_query`: Create a research query prompt

## Prerequisites

Before running the MCP server, make sure you have:

1. Python 3.10 or higher installed
2. API keys for the services you plan to use:
   - OpenAI API key
   - Tavily API key (or other search APIs you plan to use)

## Installation

1. Clone the GPT Researcher repository:
```bash
git clone https://github.com/assafelovic/gptr-mcp.git
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Copy the `.env.example` file to create a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
   - Edit the `.env` file and add your API keys and configure other settings:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

## Running the MCP Server

You can start the MCP server in two ways:

### Method 1: Directly using Python

```bash
python server.py
```

### Method 2: Using the MCP CLI (if installed)

```bash
mcp run server.py
```

Once the server is running, you'll see output indicating that the server is ready to accept connections.

## Integrating with Claude

There are two primary ways to integrate your MCP server with Claude:

1. **[API Integration](./claude-integration)** - For programmatic access through Claude API
2. **[Desktop Integration](./claude-desktop-integration)** - For using with Claude desktop application on Mac

For detailed instructions on each method, follow the links above.

## Example Usage with Claude

```
User: I'm considering investing in NVIDIA. Can you research the current state of the company, recent stock performance, latest product announcements, and analyst opinions?

Claude: I'll help you research NVIDIA for investment purposes. This will take a moment as I conduct comprehensive research to find the most up-to-date information about their stock performance, recent developments, and expert analysis.

[Claude uses conduct_research tool - this takes 30-40 seconds]

Claude: Based on my research, here's a comprehensive analysis of NVIDIA's current state:

## NVIDIA (NVDA) Current Status

### Recent Stock Performance
- Current price: $942.89 (as of my research)
- YTD performance: +90.4% 
- 52-week range: $460.30 - $974.00
- Market cap: ~$2.32 trillion

### Recent Key Developments
1. **Blackwell AI Platform**: At GTC 2024, NVIDIA unveiled the Blackwell architecture, their next-generation AI chip platform promising 4x performance improvement over Hopper. Major cloud providers (AWS, Google, Microsoft) have already committed to integrating Blackwell.

2. **Q1 FY2025 Earnings (May 2024)**: 
   - Revenue: $26.0 billion (+262% YoY)
   - Data Center revenue: $22.6 billion (+427% YoY)
   - Gross margin: 78.4%
   - Announced 10-for-1 stock split effective June 7, 2024

3. **Supply Chain Expansion**: Increased investments in manufacturing capacity with TSMC to address ongoing chip shortages for their high-demand AI GPUs.

### Analyst Consensus
- Strong Buy consensus with 37 analysts rating it "Buy," 5 "Hold," and 0 "Sell"
- Average price target: $1,042 (post-split adjusted: $104.20)
- Key bull thesis: Continued AI infrastructure spending and NVIDIA's dominant position in AI chips
- Key bear concerns: Valuation, potential competition from AMD, Intel, and custom silicon from tech giants

### Industry Position
- Dominant in AI GPU market with estimated 80-90% market share
- Expanding ecosystem through CUDA software platform and industry partnerships
- Diversifying beyond chips with DGX Cloud, AI software platforms, and automotive solutions
```

## Troubleshooting

If you encounter issues while running the MCP server:

1. Make sure your API keys are correctly set in the `.env` file
2. Check that you're using Python 3.10 or higher
3. Ensure all dependencies are installed correctly
4. Check the server logs for error messages

## Next Steps

- Explore the [MCP protocol documentation](https://docs.anthropic.com/claude/docs/model-context-protocol) to better understand how to integrate with Claude
- Learn about [GPT Researcher's core features](../getting-started/introduction) to enhance your research capabilities
- Check out the [Advanced Usage](./advanced-usage) guide for more configuration options

:-) 