# Hosted GPT Researcher MCP

HLT hosts this fork as two Railway services:

- API/frontend: `https://gpt-researcher-api-production.up.railway.app`
- MCP: `https://gpt-researcher-mcp-production.up.railway.app/mcp`

The browser frontend can load publicly, but v1 production research actions are
for authenticated REST and MCP clients.

For operational guidance, decision rules, and Sidecar/Katailyst use cases, see
[`docs/usage/owners-manual.md`](./owners-manual.md).

## MCP Client Config

Claude Code / Cursor `.mcp.json`:

```json
{
  "mcpServers": {
    "gpt-researcher": {
      "type": "http",
      "url": "https://gpt-researcher-mcp-production.up.railway.app/mcp",
      "headers": {
        "Authorization": "Bearer ${GPTR_MCP_TOKEN}"
      }
    }
  }
}
```

Claude Desktop:

```json
{
  "mcpServers": {
    "gpt-researcher": {
      "type": "http",
      "url": "https://gpt-researcher-mcp-production.up.railway.app/mcp",
      "headers": {
        "Authorization": "Bearer ${GPTR_MCP_TOKEN}"
      }
    }
  }
}
```

## MCP Curl Smoke

Local run from the repo root:

```bash
MCP_AUTH_TOKEN=dev-token \
RESEARCH_RUN_STORE_PATH=data/research_runs.sqlite3 \
OUTPUTS_DIR=outputs \
MCP_ALLOWED_HOSTS=127.0.0.1:8001,localhost:8001,127.0.0.1,localhost,0.0.0.0 \
python -m uvicorn mcp_server.server:app --host=0.0.0.0 --port=8001
```

FastMCP validates the full `Host` header, so include the local port in
`MCP_ALLOWED_HOSTS` when overriding the default.

Initialize and capture the MCP session id:

```bash
headers="$(mktemp)"
curl -sS -D "$headers" -X POST "https://gpt-researcher-mcp-production.up.railway.app/mcp" \
  -H "Authorization: Bearer $GPTR_MCP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"1.0.0"}}}'
session_id="$(awk 'tolower($1) == "mcp-session-id:" {print $2}' "$headers" | tr -d '\r' | head -1)"
```

List tools:

```bash
curl -sS -X POST "https://gpt-researcher-mcp-production.up.railway.app/mcp" \
  -H "Authorization: Bearer $GPTR_MCP_TOKEN" \
  -H "mcp-session-id: $session_id" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Call quick search:

```bash
curl -sS -X POST "https://gpt-researcher-mcp-production.up.railway.app/mcp" \
  -H "Authorization: Bearer $GPTR_MCP_TOKEN" \
  -H "mcp-session-id: $session_id" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"quick_search","arguments":{"query":"NCLEX-RN pass rate 2026","summary":true}}}'
```

## REST API Curl

Health is public:

```bash
curl -fsS "https://gpt-researcher-api-production.up.railway.app/health"
```

API calls require `X-API-Key`:

```bash
curl -sS -X POST "https://gpt-researcher-api-production.up.railway.app/api/quick_search" \
  -H "X-API-Key: $API_AUTH_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"NCLEX-RN pass rate 2026","summary":true}'
```

Deep report:

```bash
curl -sS -X POST "https://gpt-researcher-api-production.up.railway.app/report/" \
  -H "X-API-Key: $API_AUTH_KEY" \
  -H "Content-Type: application/json" \
  -d '{"task":"Research NCLEX-RN pass rate changes in 2026","report_type":"research_report","report_source":"web","tone":"Objective","repo_name":"","branch_name":"","generate_in_background":false}'
```

## Auth And Rotation

- API service secret: `API_AUTH_KEY`, sent as `X-API-Key`.
- MCP service secret: `MCP_AUTH_TOKEN`, sent as `Authorization: Bearer ...`.
- Local MCP client secret: `GPTR_MCP_TOKEN`; set it to the same value as
  `MCP_AUTH_TOKEN` for clients.
- Durable run metadata: `RESEARCH_RUN_STORE_PATH`, backed by SQLite. On Railway,
  set this to a mounted volume path such as `/data/research_runs.sqlite3`.
- Generated report/log files: `OUTPUTS_DIR`. On Railway, set this to the same
  mounted volume, such as `/data/outputs`.
- Volume permissions: Railway mounts volumes as `root`; these hosted Docker
  services set `RAILWAY_RUN_UID=0` so SQLite metadata and report files are
  writable on the mounted volume.

To rotate:

1. Set a new `API_AUTH_KEY` or `MCP_AUTH_TOKEN` in Railway.
2. Redeploy the affected service.
3. Update local client env (`API_AUTH_KEY` or `GPTR_MCP_TOKEN`).
4. Re-run the smoke commands above.

## Katailyst Integration

Katailyst integration lives outside the public GPT Researcher browser UI. The
canonical path is:

1. Register/discover `tool:gpt-researcher.mcp` in Katailyst.
2. Let agents mount the hosted GPT Researcher MCP endpoint with
   `Authorization: Bearer ${GPTR_MCP_TOKEN}`.
3. Keep Katailyst credentials in the calling agent/runtime, not in browser
   source, local storage, or a public MCP textarea.

This keeps the upstream-tracked GPT Researcher UI close to upstream while still
letting HLT agents compose GPT Researcher with Katailyst.

## UI WebSocket Smoke

After deploying API changes, verify the browser auth path and WebSocket startup
without running a full report:

```bash
.venv/bin/python scripts/smoke_websocket_ui.py \
  --ui-url https://gpt-researcher-ui.vercel.app \
  --api-url https://gpt-researcher-api-production.up.railway.app \
  --scope codebase,metrics,firecrawl \
  --allow-degraded-scope
```

The command should print `hlt_scope_active` / `hlt_scope_degraded` lines and
exit before a full report is generated. Omit `--allow-degraded-scope` when the
deployment should fail the smoke test unless all requested scopes are ready.

## Tools

- `deep_research` creates a `research_id` and returns context, sources, source
  URLs, and source count. Completed run metadata is persisted in SQLite and can
  be recovered after an MCP/API restart.
- `quick_search` returns fast search results or a summary.
- `write_report` accepts a prior `research_id`; if the hot cache was lost, it
  hydrates from persisted context and source metadata.
- `get_research_sources` accepts a prior `research_id`.
- `get_research_context` accepts a prior `research_id`.
- `research://{topic}` returns cached, persisted, or newly generated research
  context.
