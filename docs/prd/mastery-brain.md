# Mastery Brain — Product Requirements Document

**Status:** Active  
**Owner:** Alec Whitters / HLT  
**Repo:** `hlt-gpt-researcher` (Mastery Research)  
**Last updated:** 2026-07-30

## Vision

Mastery Brain is the personal research OS for HLT’s product estate. Nontechnical teammates can talk to it, see what each codebase can do, ask “can we do X?”, store vision, and watch an interactive changelog of what shipped — powered by a maxed-out GPT Researcher, a code-graph MCP over the estate repos, and a persistent Hermes agent that learns across sessions.

It leans toward **2027**: frontier models via OpenRouter (swappable), subagents for parallel research, MCP-native integrations (Katailyst2, Linear, code graph, media), and highly interactive visuals — not a static FAQ wiki.

## Personas

| Persona | Needs |
|---------|--------|
| **Nontechnical teammate** (marketing, recruiting, ops) | Plain-English answers, visuals, “can we do this?” without reading code |
| **Alec** | Store vision, steer product, deep research across repos + web + registry |
| **Agent consumers** (Katailyst2, Hermes, other MCP clients) | Reliable `deep_research` / `quick_search` / `/gather` with scope presets |

## Surfaces (UI tabs)

1. **Ask** — Existing Mastery Research console (web + scoped MCP research).
2. **Codebase** — Per-repo concept pages (mmm2, katailyst2, ebb, scrapervault, nursing-mastery) with architecture clusters, capabilities, and a “Can we do X?” box that routes to code-scoped research.
3. **Vision** — Editable markdown vision docs indexed into hybrid research context so answers cite product north star.
4. **Changelog** — Interactive visual timeline of what changed across the estate (git + Linear releases), agent-written plain English.
5. **Roadmap** — Linear projects/milestones; Productboard stub until credentials exist.

## Architecture

```
Mastery Research UI (Vercel)
  → GPT Researcher API + MCP (Railway)  [synced fork + HLT overlay]
  → Code-graph MCP (Render)             [GitNexus indexes 5 repos]
Hermes agent (Render VM)
  → mounts GPTR MCP, code graph, Katailyst2, Linear
  → Slack/Telegram gateway for the team
```

### Estate repos (code scope)

- `Awhitter/MMM2` — multimedia engine  
- `Awhitter/katailyst2` — AI primitives / registry / command hub  
- `Awhitter/evidence-based-business` (ebb) — metrics  
- `Awhitter/ScraperVault` — recruiting data backend  
- `Awhitter/nursing-mastery` — nurse-facing product surface  

Override via `HLT_CODEBASE_REPOS`.

## Data sources

| Source | Role |
|--------|------|
| Deep web (Tavily / Firecrawl) | External research |
| Code-graph MCP (`CODEGRAPH_MCP_*`) | Structural code Q&A (preferred for Code scope) |
| GitHub MCP | Fallback code/search |
| Katailyst2 MCP | Registry, skills, playbooks |
| Cloudinary | Media library |
| Metabase / Katailyst metrics | Metrics scope |
| Linear MCP | Roadmap + releases |
| Productboard | Roadmap (when keyed) |
| Vision docs (`my-docs/vision/`) | Hybrid research context |

## Model strategy

- Default frontier stack via OpenRouter (SMART / STRATEGIC / FAST LLMs configurable).
- Subagents for parallel code + web + registry retrieval.
- Hermes persistent memory + skill loop for cross-session learning.
- Swap models without code changes (env / OpenRouter).

## Success criteria

1. A marketer gets a correct, visual answer to “can MMM2 do X?” in under 2 minutes.
2. Code scope uses the code-graph MCP when configured; GitHub MCP is fallback only.
3. Vision docs appear in hybrid research citations when relevant.
4. Changelog shows at least the last 30 days of estate activity in plain English.
5. Roadmap tab reflects live Linear milestones for Nursing Mastery workspace.
6. `/gather` and hosted MCP tools remain green for Katailyst2 consumers.
7. Upstream sync remains re-applicable: HLT logic stays in overlay modules.

## Rollout phases

| Phase | Deliverable |
|-------|-------------|
| 1 | Upstream sync + tests + Railway redeploy |
| 2 | This PRD |
| 3 | Code-graph service on Render + Code scope wiring |
| 4 | Hermes on Render with Slack + MCP mounts |
| 5 | Team Brain UI tabs (Ask / Codebase / Vision / Changelog / Roadmap) |

## Cost envelope (indicative)

- Render: code-graph + Hermes VMs (~$7–25/mo each on starter, plus disk)
- Railway: existing API + MCP
- Vercel: existing UI
- LLM/search: usage-based (OpenRouter, Tavily, etc.)

## Non-goals

- Replacing Katailyst2 as the registry / command hub
- Public library listing of internal UI components without explicit publish
- Writing strategy docs outside the product vision store / One Place capture path
