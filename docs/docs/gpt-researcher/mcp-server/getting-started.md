---
sidebar_position: 1
---

# Getting Started with MCP Server

The GPT Researcher MCP Server provides Model Context Protocol (MCP) integration for GPT Researcher, allowing AI assistants to perform autonomous, comprehensive web research and generate reports via the MCP protocol.

## Why GPT Researcher MCP?

While many AI assistants can already access web search tools, GPT Researcher MCP offers significant advantages:

### Beyond Simple Web Search

Standard web search tools return raw search results that:
- Require manual filtering by the AI
- Often include irrelevant or low-quality sources
- Don't organize information for optimal comprehension
- Waste valuable context window space with redundant content

**GPT Researcher performs autonomous, comprehensive research** - not just search. It:
- Intelligently explores multiple sources based on relevancy
- Validates information across sources for reliability
- Focuses only on the most up-to-date and pertinent information
- Optimizes content for LLM context windows
- Structures information for better AI reasoning

While it takes slightly longer (30-40 seconds) than a standard web search, it delivers:

1. **Higher quality information**: Only the most reliable and relevant sources
2. **Better organized context**: Content structured for optimal AI comprehension
3. **More comprehensive results**: Multi-source research, not just top search hits
4. **Context optimization**: Intelligently fits within LLM context windows
5. **Improved reasoning**: Helps AI assistants create better responses and reports

The result? LLMs powered by GPT Researcher produce dramatically better responses to research queries, with more accurate, up-to-date, and comprehensive information.

## Features

- Autonomous web research capabilities through GPT Researcher
- MCP protocol support for AI assistants like Claude
- Research report generation in different formats
- Access to research sources, context, costs, and images
- Context optimization for different LLM requirements

## Prerequisites

Before running the MCP server, make sure you have:

1. Python 3.10 or higher installed
2. API keys for the services you plan to use:
   - OpenAI API key
   - Tavily API key (or other search APIs you plan to use)

## Installation

1. Clone the GPT Researcher repository:
```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

2. Install the mcp-server dependencies:
```bash
cd mcp-server
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
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

## Using with Claude or Other MCP Clients

The MCP server exposes the following capabilities to AI assistants:

### Resources
- `research_resource`: Get web resources related to a given task via research.

### Primary Tools

- `conduct_research`: Performs autonomous web research on a topic, finding the most reliable and relevant information
- `write_report`: Generate a report based on research results
- `get_research_sources`: Get the sources used in the research
- `get_research_context`: Get the full context of the research

### Prompts

- `research_query`: Create a research query prompt

## Example Usage with Claude

Here's an example of how a user might interact with Claude to use GPT Researcher for time-sensitive, real-time information:

```
User: I'm considering investing in NVIDIA. Can you research the current state of the company, recent stock performance, latest product announcements, and analyst opinions?

Claude: I'll help you research NVIDIA for investment purposes. This will take a moment as I conduct comprehensive research to find the most up-to-date information about their stock performance, recent developments, and expert analysis.

[Claude uses conduct_research tool - this takes 30-40 seconds but provides high-quality, real-time information]

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

### Alternative Example: Sports Updates

```
User: Can you provide me with the latest updates on the English Premier League? I'm particularly interested in the current standings, recent transfers, and any major news about top teams.

Claude: I'll research the latest English Premier League updates for you. This will take a moment as I gather comprehensive information about current standings, recent transfers, and major team news.

[Claude uses conduct_research tool - this takes 30-40 seconds but provides up-to-date sports information]

Claude: Here are the latest updates on the English Premier League (as of my research):

## Current EPL Standings (Top 6)
1. **Manchester City** - 91 points (Champions)
2. **Arsenal** - 89 points 
3. **Liverpool** - 82 points
4. **Aston Villa** - 68 points (Champions League qualification)
5. **Tottenham** - 65 points
6. **Chelsea** - 63 points

## Recent Major Transfers & Rumors
1. **Confirmed Deals**:
   - Chelsea signed Tosin Adarabioyo from Fulham on a free transfer
   - Cole Palmer signed new long-term contract with Chelsea until 2033
   - Kieran Trippier extended his contract with Newcastle United

2. **Active Transfer Rumors**:
   - Manchester United pursuing PSG's Manuel Ugarte as midfield reinforcement
   - Arsenal in advanced talks with Bologna for Riccardo Calafiori
   - Liverpool showing interest in Anthony Gordon from Newcastle
   - Chelsea negotiating with Napoli for Victor Osimhen

## Major Recent Developments
1. **Managerial Changes**:
   - Ange Postecoglou remains at Tottenham despite Bayern Munich interest
   - Jurgen Klopp departed Liverpool after nine years, replaced by Arne Slot
   - Erik ten Hag retained by Manchester United after FA Cup victory

2. **Financial Updates**:
   - Premier League clubs agreed to reforms to financial rules, replacing Profit and Sustainability Rules (PSR)
   - Everton's potential takeover by 777 Partners facing regulatory hurdles

3. **2024/25 Season**:
   - New season scheduled to start on August 17, 2024
   - Introduction of semi-automated offside technology confirmed
   - Manchester City entering as defending champions seeking fifth consecutive title

This sports example further demonstrates GPT Researcher's ability to provide real-time information across diverse domains, compiling facts from multiple sources into a comprehensive, well-structured response.

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