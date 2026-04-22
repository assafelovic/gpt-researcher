# GPT Researcher Hosted MCP Endpoint

This directory is kept as the upstream documentation location, but the HLT
hosted MCP implementation lives in the root Python package `mcp_server/` so it
can import the local `gpt_researcher` library from the repo root.

Hosted endpoint:

```text
https://gpt-researcher-mcp-production.up.railway.app/mcp
```

Auth:

```text
Authorization: Bearer $GPTR_MCP_TOKEN
```

Public health check:

```text
https://gpt-researcher-mcp-production.up.railway.app/health
```

## Tools

- `deep_research(query, report_type?, report_source?, tone?)`
- `quick_search(query, summary?, domains?)`
- `write_report(research_id, custom_prompt?)`
- `get_research_sources(research_id)`
- `get_research_context(research_id)`

Resource:

- `research://{topic}`

Prompt:

- `research_query(topic, goal, report_format?)`

## Local Run

From the repo root:

```bash
MCP_AUTH_TOKEN=dev-token \
python -m uvicorn mcp_server.server:app --host=0.0.0.0 --port=8001
```

The Railway MCP service also runs from the repo root. Do not set the service
root directory to `mcp-server/`; that would hide the parent package.
