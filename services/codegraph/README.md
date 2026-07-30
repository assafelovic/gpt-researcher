# HLT Codegraph MCP (GitNexus)

Indexes the five estate repos into a GitNexus knowledge graph and exposes
structural tools over streamable HTTP for GPT Researcher + Hermes.

## Tools

- `list_repos`, `query`, `context`, `impact`, `trace`, `repo_overview`

## Env

| Var | Purpose |
|-----|---------|
| `GITHUB_TOKEN` | Clone private/public repos |
| `CODEGRAPH_MCP_TOKEN` | Bearer auth for `/mcp` |
| `CODEGRAPH_REPOS` | Optional `slug\|org/repo,...` override |
| `CODEGRAPH_REINDEX_HOURS` | Background reindex interval (default 24; `0` off) |
| `CODEGRAPH_SKIP_INDEX_ON_BOOT` | `1` to skip boot reindex |
| `PORT` | Bind port (Render sets this) |

## Local

```bash
docker build -t hlt-codegraph .
docker run --rm -p 8080:8080 \
  -e GITHUB_TOKEN \
  -e CODEGRAPH_MCP_TOKEN=dev \
  -v codegraph-data:/data \
  hlt-codegraph
```

Point GPT Researcher at it:

```
CODEGRAPH_MCP_URL=https://<service>/mcp
CODEGRAPH_MCP_TOKEN=dev
```
