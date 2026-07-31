# Mastery Research (GPT Researcher) — tier-1 estate capability

Deep research engine + team brain for the HLT estate. Any estate agent or
teammate can run cited deep research through it instead of building their own
research loop.

## Surfaces

- Human UI: https://gpt-researcher-ui.vercel.app (branded Mastery Research).
  Brain tabs: Ask, Audience, Codebase, Library, Vision, Changelog, Roadmap.
- HTTP API: https://gpt-researcher-api-production.up.railway.app
  (`POST /report/` for deep reports, `POST /gather` for Katailyst typed
  findings, `GET /api/brain/*` for team-brain payloads; auth `X-API-Key`).
- MCP server: https://gpt-researcher-mcp-production.up.railway.app/mcp
  (Bearer auth). Tools: `deep_research`, `quick_search`, `write_report`,
  `get_research_sources`, `get_research_context`; resource `research://{topic}`.

## Scope presets (server-side, token-free for browsers)

`hlt_research_scope` booleans on `/report/`: `codebase` (GitNexus codegraph +
GitHub MCP over the 5 estate repos), `cms` (Katailyst2 registry), `qbank`
(partner API when configured, Katailyst path meanwhile), `metrics` (Metabase),
`firecrawl` (deep web + Apify MCP), `media` (Cloudinary read-only),
`audience` (nurse forums, verbatim quotes with receipts + voice-of-nurse
corpus), `recruiting` (nursingmastery.com content inventory + gap analysis).
Depth: `fast | balanced | deep`. Mode: `standard | top1` — top1 runs the
"study the best on earth, distill mechanisms, rhyme for nursing, verify
against audience truth" doctrine.

## Memory

Finished reports persist and are searchable (`/api/brain/library`); new runs
automatically consult the top related prior reports so research compounds.

## When to use

- Deep customer/competitive/audience research with citations.
- "Can our estate do X?" codebase questions for non-engineers.
- Weekly audience sweeps (automated Monday GitHub Action).

Owner repo: Awhitter/hlt-gpt-researcher-1 (fork of assafelovic/gpt-researcher,
weekly upstream-sync automation).
