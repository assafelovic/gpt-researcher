# MCP Integration Reference

## Table of Contents
- [Overview](#overview)
- [Configuration](#configuration)
- [Strategy Options](#strategy-options)
- [Processing Logic](#processing-logic)

---

## Overview

MCP (Model Context Protocol) enables research from specialized data sources (GitHub, databases, APIs) alongside web search.

---

## Configuration

```python
researcher = GPTResearcher(
    query="...",
    mcp_configs=[
        {
            "name": "github",                    # Server name
            "command": "npx",                    # Command to start
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": "..."},      # Environment vars
        },
        {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem", "/docs"],
        },
        {
            "name": "remote",
            "connection_url": "ws://server:8080",  # WebSocket connection
            "connection_type": "websocket",
            "connection_token": "auth_token",
        }
    ],
    mcp_strategy="fast",  # fast, deep, disabled
)
```

---

## Strategy Options

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `fast` (default) | Run MCP once with original query, cache results | Performance-focused |
| `deep` | Run MCP for every sub-query | Maximum thoroughness |
| `disabled` | Skip MCP entirely | Web-only research |

---

## Processing Logic

**File:** `gpt_researcher/skills/researcher.py`

```python
# At start of research (for 'fast' strategy)
if mcp_strategy == "fast":
    mcp_context = await self._execute_mcp_research_for_queries([query], mcp_retrievers)
    self._mcp_results_cache = mcp_context  # Cache for reuse

# During sub-query processing
if mcp_strategy == "fast" and self._mcp_results_cache is not None:
    mcp_context = self._mcp_results_cache.copy()  # Reuse cache
elif mcp_strategy == "deep":
    mcp_context = await self._execute_mcp_research_for_queries([sub_query], mcp_retrievers)
```

### WebSocket Request Example

```json
{
    "task": "Research query",
    "report_type": "research_report",
    "mcp_enabled": true,
    "mcp_strategy": "fast",
    "mcp_configs": [
        {
            "name": "github",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": "..."}
        }
    ]
}
```
