# HLT Hermes Brain (Render)

Persistent NousResearch Hermes agent for the Mastery Brain: Slack gateway,
memory/skills on a Render disk, MCP mounts to GPT Researcher, codegraph,
Katailyst2, and Linear.

## Env

| Var | Purpose |
|-----|---------|
| `OPENROUTER_API_KEY` | Frontier models |
| `HERMES_MODEL` | Optional model override |
| `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` | Slack gateway |
| `GPTR_MCP_URL` / `GPTR_MCP_TOKEN` | Hosted researcher MCP |
| `CODEGRAPH_MCP_URL` / `CODEGRAPH_MCP_TOKEN` | Estate code graph |
| `KATAILYST2_MCP_URL` / `KATAILYST2_MCP_TOKEN` | Registry |
| `LINEAR_MCP_URL` / `LINEAR_MCP_TOKEN` | Roadmap (optional) |
| `HERMES_HOME` | Persistent disk path (default `/data/hermes`) |

## Enabling the full Slack gateway (one-time, ~3 minutes in a browser)

The service ships in **readiness-gateway mode** (health endpoint only) until
Slack tokens exist. Everything else — OpenRouter key, MCP mounts, seeded
memory, persistent disk — is already wired. To go live on Slack:

1. Open https://api.slack.com/apps → **Create New App** → **From an app
   manifest** → choose the HLT workspace → paste
   [`slack-app-manifest.yaml`](./slack-app-manifest.yaml) → **Create**.
2. On the app page: **Basic Information → App-Level Tokens → Generate Token**
   with scope `connections:write`. Copy the `xapp-…` token.
3. **Install App** (left sidebar) → **Install to Workspace** → copy the
   **Bot User OAuth Token** (`xoxb-…`).
4. In Render → `hlt-hermes` → Environment, set:
   - `SLACK_BOT_TOKEN` = the `xoxb-…` token
   - `SLACK_APP_TOKEN` = the `xapp-…` token
   - `HERMES_ENABLE_GATEWAY` = `1`
5. Save (Render redeploys automatically). `/health` switches from
   `readiness_gateway` to the real Hermes gateway.

## Smoke

After deploy: `curl https://<service>/health` then DM the Slack bot
“what can scrapervault do?” and confirm it hits codegraph + researcher.
