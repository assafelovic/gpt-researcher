# Branding And Catalyst Integration Options

Last updated: 2026-04-22

This repo is an upstream-tracked GPT Researcher fork, so the right posture is
branding and integration as a thin overlay. Keep the upstream research engine
and UI structure recognizable; make HLT/Catalyst identity appear through config,
chrome, metadata, docs, and the calling surfaces around it.

## What Is Implemented Now

The hosted Next.js UI has a small HLT/Mastery/Catalyst branding overlay:

- App title: `Mastery Research`
- Header mark: HLT Mastery app icon
- Header link: `Open Katailyst`
- Hero copy: "Research anything with Mastery-grade context."
- Research scope selector: Code files, CMS/Registry, Metrics, High-quality crawl
- Footer: HLT attribution while preserving GPT Researcher credit
- PWA metadata/manifest: HLT research workspace naming
- Color direction: HLT blue `#155EEF`, deep navy `#0B2B33`, warm white direction

The overlay is controlled by public frontend env vars:

```bash
NEXT_PUBLIC_HLT_BRANDING=1
NEXT_PUBLIC_HLT_BRAND_NAME="Mastery Research"
NEXT_PUBLIC_HLT_PLATFORM_NAME="Katailyst"
NEXT_PUBLIC_HLT_OWNER_NAME="HLT"
NEXT_PUBLIC_HLT_BRAND_SUBTITLE="Katailyst research console"
NEXT_PUBLIC_HLT_HERO_TITLE="Research anything with Mastery-grade context."
NEXT_PUBLIC_HLT_HERO_NOTE="Source-backed web, codebase, CMS, and metrics research through GPT Researcher."
NEXT_PUBLIC_HLT_BRAND_ICON="/img/hlt-mastery-icon.png"
NEXT_PUBLIC_KATAILYST_URL="https://www.katailyst.com"
NEXT_PUBLIC_GPTR_UI_URL="https://gpt-researcher-ui.vercel.app"
```

Set `NEXT_PUBLIC_HLT_BRANDING=0` if you need to temporarily fall back to
upstream GPT Researcher labels.

## Integration Options

### Option 1: Branded Standalone UI

Keep GPT Researcher at its own URL and make it look like part of the HLT stack.

Best when:

- Humans need a stable research workspace.
- You want the least coupling to Catalyst/Katailyst internals.
- You want upstream syncs to stay easy.

Current URL:

```text
https://gpt-researcher-ui.vercel.app
```

This is the option implemented now.

### Server-Side Research Scope Presets

The UI checkboxes are intentionally token-free. They send
`hlt_research_scope` metadata over the existing WebSocket start payload. The
backend expands that metadata in `backend/server/hlt_extensions.py`.

| Checkbox | What it does now | Required env for full power |
| --- | --- | --- |
| Code files | Adds codebase instructions and requests Katailyst + GitHub MCP presets | `KATAILYST_MCP_TOKEN`, optional `GITHUB_MCP_URL` / `GITHUB_MCP_TOKEN` |
| CMS + Registry | Adds Katailyst registry/CMS instructions and requests the Katailyst MCP preset | `KATAILYST_MCP_TOKEN` |
| Metrics | Adds metrics instructions and requests Metabase; falls back to Katailyst metrics tools when direct Metabase MCP is unset | `KATAILYST_MCP_TOKEN`; optional `METABASE_MCP_URL` / `METABASE_MCP_TOKEN` |
| High-quality crawl | Adds extraction-quality instructions | `SCRAPER=firecrawl`, `FIRECRAWL_API_KEY` |

Server-side preset env:

```bash
KATAILYST_MCP_URL=https://www.katailyst.com/mcp
KATAILYST_MCP_TOKEN=...
GITHUB_MCP_URL=...
GITHUB_MCP_TOKEN=...
METABASE_MCP_URL=...
METABASE_MCP_TOKEN=...
```

If direct Metabase env is missing, Metrics uses the Katailyst MCP fallback.
If another preset env var is missing, the backend skips that MCP server and logs a
warning; the research run still proceeds with the remaining available sources.

### Option 2: Iframe Inside Catalyst

Add a Catalyst dashboard page that embeds the hosted GPT Researcher UI in an
iframe.

Best when:

- You want users to enter through Catalyst.
- You want minimal engineering effort.
- You can accept two apps talking through browser boundaries.

Tradeoffs:

- Fastest to ship.
- Keeps secrets server-side if GPT Researcher UI keeps using its existing API
  proxy/token flow.
- Less native than a real Catalyst page.
- Cross-app auth and height/resizing can be clunky.

Recommended route shape:

```text
https://www.katailyst.com/dashboard-cms/tools/gpt-researcher
```

### Option 3: Native Catalyst Research Page

Build a Catalyst page that calls the GPT Researcher API/MCP directly and renders
research progress/results with Catalyst components.

Best when:

- You want it to feel fully native.
- You want registry context, saved research packets, run history, and Sidecar
  handoff in one place.
- You are ready to own a Catalyst-specific frontend for the research flow.

Tradeoffs:

- Strongest user experience.
- More code to maintain.
- Must mirror the WebSocket/report/chat behavior from GPT Researcher.

Recommended architecture:

```text
Catalyst page -> Catalyst server route -> GPT Researcher REST/MCP -> Catalyst UI
```

Do not expose `API_AUTH_KEY`, `MCP_AUTH_TOKEN`, `GPTR_MCP_TOKEN`, or Katailyst
tokens to the browser.

### Option 4: Agent-First, No New Human UI

Keep the human UI separate and make Catalyst/Katailyst the routing layer for
agents.

Best when:

- The primary users are agents, not humans.
- Sidecar, Claude Code, Cursor, or hosted agents should call GPT Researcher as
  a tool.
- You want the smallest code footprint.

Current path:

```text
Katailyst discover -> tool:gpt-researcher.mcp -> GPT Researcher MCP -> Sidecar/specialist output
```

This is the strongest fit for the "upstream-friendly fork" constraint.

## Recommended Path

Use all three layers, but in this order:

1. Keep the standalone UI branded. This is already done.
2. Add an iframe page inside Catalyst for operator convenience.
3. Wire Sidecar/Katailyst workflows to call `tool:gpt-researcher.mcp` for
   research packets.
4. Build a native Catalyst research page only after the workflow proves it
   deserves the extra ownership.

## Making It Stronger

### Research Quality

Use the right retriever/scraper mix:

| Goal | Suggested config | Notes |
| --- | --- | --- |
| Fast general web research | `RETRIEVER=tavily`, `SCRAPER=tavily_extract` | Good default for production speed |
| Higher scrape quality | `SCRAPER=firecrawl` | Use when pages are hard to parse or markdown quality matters |
| Broader source coverage | `RETRIEVER=tavily,exa` or `RETRIEVER=tavily,bing` | Requires provider keys; can increase cost/time |
| Academic/context-specific research | `RETRIEVER=arxiv,pubmed_central,tavily` | Use for research-heavy or clinical/academic topics |
| Agent/tool-aware research | `RETRIEVER=tavily,mcp`, `MCP_STRATEGY=fast` | Useful when MCP sources are configured intentionally |

For Firecrawl:

```bash
SCRAPER=firecrawl
FIRECRAWL_API_KEY=...
# Optional for self-hosted Firecrawl:
FIRECRAWL_SERVER_URL=...
```

### Speed

For faster UI/API runs:

```bash
MAX_ITERATIONS=2
TOTAL_WORDS=900
DEEP_RESEARCH_BREADTH=2
DEEP_RESEARCH_DEPTH=1
DEEP_RESEARCH_CONCURRENCY=2
SCRAPER=tavily_extract
```

Use this for social/email topic sweeps, quick briefs, and early exploration.

### Depth

For higher-quality deep dives:

```bash
MAX_ITERATIONS=3
TOTAL_WORDS=1800
DEEP_RESEARCH_BREADTH=4
DEEP_RESEARCH_DEPTH=2
DEEP_RESEARCH_CONCURRENCY=4
SCRAPER=firecrawl
```

Use this for competitive analysis, article briefs, recruiting market scans, and
education/source packets. Watch provider rate limits.

### Cost Control

- Make agents call `quick_search` before `deep_research`.
- Use narrower queries with audience, product, geography, and date context.
- Save research packets in Sidecar/MasteryPublishing metadata when they feed a
  real output.
- Track cost/latency by caller: UI, REST, MCP, Sidecar, automation.

### Reliability

- Keep `/health` smoke tests for API and MCP.
- Keep the WebSocket smoke test before UI deploys.
- Use hosted scrapers (`tavily_extract` or `firecrawl`) instead of browser
  scraping on Railway unless there is a clear reason.
- Lower `MAX_SCRAPER_WORKERS` and add `SCRAPER_RATE_LIMIT_DELAY` if Firecrawl
  rate limits appear.

## What Not To Do

- Do not put Katailyst secrets in the browser.
- Do not fork the GPT Researcher UI into a completely custom product unless
  this becomes a major owned HLT surface.
- Do not make GPT Researcher depend on Katailyst for every public research run.
- Do not bury GPT Researcher behind Catalyst before the standalone UI and MCP
  endpoint are stable.

The best operating model is: Catalyst/Katailyst is the docs index and routing
brain, GPT Researcher is the external research engine, Sidecar turns research
into production outputs, and this repo remains a thin upstream-friendly fork.
