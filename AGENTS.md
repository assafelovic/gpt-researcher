# GPT Researcher — AGENTS.md

> Agent orientation for this repo. **Read this BEFORE making changes.** This is the
> AGENTS.md spec (agents.md, formalized 2025) — the de-facto agent README adopted
> by Cursor, Claude Code, OpenAI, Sourcegraph, Factory.

## What this repo is

Research orchestration lane. Currently 6 commits diverged from upstream (24 behind) — sync before doing orchestrate-adjacent work. Used for deep customer/competitive research that feeds article writing.

## Where it sits in the HLT ecosystem

This repo is one of **15 sibling repos under `~/hlt/`** that share the
**Katailyst registry** as their capability brain (1,663 entities, 11,151
graph links, 30+ MCP tools). The full ecosystem map lives at:

- **Master:** `~/hlt/katailyst/docs/ecosystem-map/05-llms-ecosystem-master.md`
- **Atlas:** `~/hlt/katailyst/docs/ecosystem-map/01-ecosystem-atlas-master.md`
- **Repo runtime ledger:** `~/hlt/katailyst/docs/ecosystem-map/03-repo-runtime-ledger.md`

Sibling repos: `katailyst, sidecar, mastery-publishing, multimedia-mastery,
engage, jobs, forum-template, agent-canvas, brand-design-lab,
evidence-based-business, gpt-researcher, mastra, operator-evals, paperclip,
research-team`.

## Tools available in this repo (auto-discovered via `.mcp.json`)

Drop into this repo with Claude Code / Cursor / any MCP client and the
following servers auto-mount from `.mcp.json`:

1. **`katailyst`** (HTTP, hosted) — the registry. Tools: `discover`, `traverse`,
   `get_entity`, `registry_capabilities`, `registry_health`, `registry_agent_context`,
   `katailyst_orchestrate`, `tool_describe`/`tool_execute`, `memory_query`/`memory_write`.
   First call to make in any new task: `discover` with a 2-sentence intent.
2. **`multimediaMastery`** (HTTP, hosted) — image / video / TTS generation.
   Live at `multimediamastery.vercel.app/api/media/v1/*`. Default image model:
   FAL nano-banana-2. Cloudinary upload server-side.
3. **`axon-codegraph`** (stdio) — local code graph index. Tools: `query`,
   `context`, `impact`, `dead-code`, `cypher`. Run `axon status` from this
   repo's root to confirm freshness.

## Rules of engagement

1. **Katailyst first** — for any task that decomposes into multiple facets,
   call `discover` against the registry before assuming what's available.
   Many things you might want to build already exist as skills, KBs, prompts,
   playbooks, rubrics, schemas.
2. **Axon second** — for code understanding inside this repo, prefer
   `axon query "..."` over grep. The graph captures call chains + dead code +
   coupling that plain grep misses.
3. **No stale docs** — if you change behavior that this AGENTS.md describes,
   update this file in the same commit.
4. **Registry counts rule** — when surfacing a count from the registry,
   use `registry_capabilities` full-scope (System + Org merged). Don't quote a
   single-slice number as "the" count.
5. **Status lifecycle** — registry entities use `staged → curated → published →
   deprecated → archived`. There is **no `draft` status**. Run-step statuses
   are `pending, running, completed, failed, skipped` (no `blocked`).

## Read first (in order)

1. `llms.txt` — repo orientation auto-generated nightly, link cross-repo
2. `README.md` — human-facing overview if present
3. `package.json` (or `pyproject.toml` / `Cargo.toml`) — stack + scripts
4. The "Inspect first in this repo" list in `llms.txt`

## Inspecting the live system

- **Cron status:** `~/hlt/katailyst/.github/workflows/repo-hygiene-nightly.yml`
- **Registry health:** call `registry_health` MCP tool, or hit
  `https://www.katailyst.com/mcp` (needs Bearer auth)
- **Drift report:** `bash ~/.openclaw/workspace/system/check-llms-drift.sh`

## Honest scope of this stub

This file is a **stub auto-generated 2026-04-17** by the observability +
discoverability perfection arc (see
`~/hlt/katailyst/docs/planning/active/2026-04-17-observability-discoverability-perfection.md`).
It is the same shape across all 15 hlt repos so an agent landing cold has
a consistent first read. Per-repo specifics belong in `llms.txt` (which IS
maintained nightly from the canonical Obsidian system maps).

If you make a meaningful behavior change in this repo, edit this file by
hand to capture the new agent-relevant constraints. Don't let the
auto-generated stub become the only word on the repo's actual rules.
