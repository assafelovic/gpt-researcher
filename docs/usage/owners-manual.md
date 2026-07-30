# GPT Researcher Owner's Manual

Last updated: 2026-04-22

This is the operator guide for HLT's hosted GPT Researcher setup. It explains
what exists, who should use each surface, how agents should call it, and where
it fits with Katailyst and Sidecar.

The main rule: keep this repo close to upstream. Put HLT-specific behavior in
deployment scripts, docs, registry records, client config, or isolated HLT
modules. Do not turn the upstream GPT Researcher app into a custom HLT product
unless there is a clear reason that cannot live outside the fork.

## Live Surfaces

| Surface | URL | Best for | Auth |
| --- | --- | --- | --- |
| Browser UI | `https://gpt-researcher-ui.vercel.app` | Human research sessions and visual report flow | Public page load; research calls use server token flow |
| API | `https://gpt-researcher-api-production.up.railway.app` | Scripts, Sidecar server routes, one-off REST clients | `X-API-Key: $API_AUTH_KEY` |
| MCP | `https://gpt-researcher-mcp-production.up.railway.app/mcp` | Agents, Claude Code, Claude Desktop, Cursor, Katailyst-discovered tool use | `Authorization: Bearer $GPTR_MCP_TOKEN` |
| Katailyst2 Registry | `https://katailyst2.vercel.app/mcp` | Discovery, routing, tool metadata, capability graph | Katailyst2 `kata_…` bearer token |

Health checks:

```bash
curl -fsS https://gpt-researcher-api-production.up.railway.app/health
curl -fsS https://gpt-researcher-mcp-production.up.railway.app/health
```

Connection details and raw curl examples live in
[`docs/usage/hosted-mcp.md`](./hosted-mcp.md).

Branding, Catalyst embedding options, and performance configuration guidance
live in [`docs/usage/branding-and-catalyst-options.md`](./branding-and-catalyst-options.md).

The browser UI is now branded as `Mastery Research`. Its launch screen includes
research-scope controls for Code files, CMS/Registry, Metrics, and High-quality
crawl. Those controls do not expose secrets to the browser; the backend expands
them into server-side MCP presets from Railway env. If a selected scope is not
configured, the run continues with a `hlt_scope_status` event that names the
active and degraded scopes.

## What Your Agents Can Do

Any agent with the MCP token can mount the hosted MCP endpoint and use GPT
Researcher from anywhere. In this repo, `.mcp.json` already defines the
`gpt-researcher` server:

```json
{
  "type": "http",
  "url": "https://gpt-researcher-mcp-production.up.railway.app/mcp",
  "headers": {
    "Authorization": "Bearer ${GPTR_MCP_TOKEN}"
  }
}
```

That gives agents these tools:

| Tool | Use it when | Output |
| --- | --- | --- |
| `quick_search` | You need a fast cited lookup, topic scan, or "is this worth researching?" check | Search results or summary plus metadata |
| `deep_research` | You need a serious context packet before writing, planning, or deciding | `research_id`, context, sources, source URLs, source count |
| `write_report` | You already ran `deep_research` and want a polished report from that research state | Report text |
| `get_research_sources` | You want the source list for an existing `research_id` | Sources and URLs |
| `get_research_context` | You want the raw research context for an existing `research_id` | Context packet |
| `research://{topic}` | You want MCP resource-style access to cached or newly generated context | Research context |

The MCP service keeps a bounded hot cache for live `GPTResearcher` objects and a
SQLite metadata store for completed research context, source metadata, status,
and report paths. Configure `RESEARCH_RUN_STORE_PATH` and `OUTPUTS_DIR` on a
Railway volume when restart recovery matters. Railway volumes mount as `root`,
so the hosted Docker services also set `RAILWAY_RUN_UID=0` to make the mounted
SQLite and output paths writable.

## Content Machine And Admin Handoff

GPT Researcher should provide cited research context to the content machine; it
should not own article drafting, admin UI controls, forum posting, replies, or
infographic generation. Wire those capabilities through the calling HLT systems:

- Research: `tool:gpt-researcher.mcp`, using `quick_search` or
  `deep_research` before content generation.
- Articles: `playbook:make-article` or `playbook:create-article` in Katailyst,
  usually executed from Sidecar/admin with GPT Researcher context attached.
- Infographics and visuals: `skill:create-multimedia`,
  `skill:image-prompting`, and the Multimedia Mastery/Cloudinary lane.
- Social and community posts: `playbook:make-social`, with distribution gated
  by verified provider targets.
- Forums: forum-template must expose write endpoints for threads/comments
  before agents can post or reply. Until then, GPT Researcher can only supply
  research packets and suggested responses for review.

## When To Use Which Surface

Use the browser UI when:

- A human wants to watch a research run unfold.
- You want the existing GPT Researcher report workflow and downloads.
- You are debugging user-facing WebSocket progress behavior.

Use the REST API when:

- A server route, script, or automation needs a straightforward HTTP call.
- You want `/api/quick_search` or `/report/` without MCP session handling.
- Sidecar wants to call GPT Researcher from its own backend and pass the result
  into a specialist as `research_context`.

Use MCP when:

- An agent is deciding which research tool to use.
- Claude Code, Claude Desktop, Cursor, or another MCP client should call tools
  directly.
- Katailyst should discover GPT Researcher as a registered capability.
- You want stateful `deep_research` -> `write_report` -> `get_sources` flow.

Use Katailyst when:

- You need capability discovery, playbook routing, graph context, prompts,
  rubrics, or HLT-specific orchestration.
- You want an agent to choose between GPT Researcher, Firecrawl, Tavily, Brave,
  Perplexity, internal KBs, or Sidecar specialists.

## Default Research Pattern

For most agent work, do this:

1. Ask Katailyst `discover` what capability should handle the task.
2. Use `quick_search` to scope the topic and avoid wasting deep-research cost.
3. Use `deep_research` only when the next step needs durable context, a source
   packet, or a report-grade synthesis.
4. Pull `get_research_context` and hand that into Sidecar, a writer, a rubric,
   or a decision memo.
5. Use `write_report` only after the research context is good enough.

In prompt form:

```text
Use Katailyst first to discover relevant HLT context. If web research is needed,
call gpt-researcher quick_search for a fast scan. Escalate to deep_research only
if the result will feed a content brief, decision memo, competitive analysis, or
source-backed article. Return sources separately from recommendations.
```

## Sidecar Use Cases

I inspected `/Users/alecwhitters/hlt/sidecar` and found GPT Researcher fits best
as a research-context provider before Sidecar specialists draft, grade, or
publish. The right integration is Sidecar/Katailyst calling GPT Researcher, then
passing the resulting context into the existing domain flows. Do not hardwire
Sidecar behavior into this GPT Researcher fork.

### Articles

Sidecar's article lane already starts with research, then topic selection,
outline, draft, media, grading, and publishing to MasteryPublishing. GPT
Researcher should be used for:

- Topic gap scans: "Which NCLEX/FNP topics have student demand but weak
  competitor coverage?"
- SERP and competitor briefs before article selection.
- Source packets for deep-dive articles, especially when the writer needs
  cited background.
- Freshness checks before updating old resources.

Recommended flow:

```text
Katailyst discover -> gpt-researcher quick_search -> gpt-researcher deep_research
-> Sidecar article specialist receives research_context -> draft -> rubric -> publish.
```

### Social

The social lane is explicitly research-heavy: audience voice, demand signals,
top performers, cross-industry patterns, existing articles, and QBank context.
GPT Researcher should be used for:

- Weekly topic sweeps across a product or exam.
- Cross-industry structural mining support before the social specialist adapts
  patterns to HLT channels.
- Evidence packets for "why this post now?" decisions.
- Follow-up context when a viral angle needs proof before drafting.

Use `quick_search` for broad scans and `deep_research` for campaign-level
research packets.

### Ads

The ads lane requires audience and competitor research before copy. GPT
Researcher should be used for:

- Competitor landing-page and offer-angle analysis.
- Market-positioning briefs before A/B copy generation.
- "What objections are competitors addressing?" research.
- Evidence for claims, proof points, and price/value framing.

Keep conversion metrics, spend, and account performance inside the ads/metrics
systems. GPT Researcher is for external market context, not internal truth.

### Email

The email lane researches audience voice, segment health, recent article
library, and past performance before recommending sends. GPT Researcher should
be used for:

- Weekly send theme discovery.
- External trend/news angle validation.
- Competitor newsletter scan.
- Segment-specific objection and motivation research.

Marketo and internal performance data stay authoritative. GPT Researcher adds
outside context.

### Education

The education lane builds study guides and teaching assets from bundles,
teaching principles, and topic research. GPT Researcher should be used for:

- Current standard/background scans before study-guide creation.
- Clinical topic context packets for writers.
- Blueprint-aligned topic expansion.
- Source lists for reviewer audit.

Guardrail: do not treat GPT Researcher as final clinical authority. It gathers
and synthesizes sources; HLT still needs clinical/editorial review before
publishing health education material.

### Metrics

The metrics lane focuses on internal performance, dashboards, and external
competitive intelligence. GPT Researcher should be used for:

- Explaining external context behind performance changes.
- Competitor movement or market change briefs.
- Weekly/monthly performance narrative enrichment.
- Cross-industry tactics to test after internal metrics show a bottleneck.

Internal analytics are the source of truth. GPT Researcher answers "what might
be happening outside our walls?"

### Recruiting

Recruiting specialists already accept `research_context` and require claims to
trace to either context or the curated recruiting corpus. GPT Researcher should
be used for:

- Compensation, benefits, and labor-market scans.
- Employer-value-proposition research.
- Regional nursing hiring trend briefs.
- Prep checklists that need current public context.

This is a strong deep-research use case because source traceability matters.

### Multimedia

Multimedia is not primarily a research lane, but it benefits from researched
creative briefs. GPT Researcher should be used for:

- Evidence-backed image/video brief context.
- Competitor visual-language scans.
- Topic background before creating educational visuals.
- Source context for infographics or explainers.

The handoff should be: research packet -> visual rationale -> Multimedia
Mastery generation, not GPT Researcher generating final media.

## Deep Dive Playbook

Use this when you want a serious research pass before a campaign, article
series, product decision, or content strategy.

1. Define the decision:

```text
What decision will this research change? Who is the audience? What output is
needed: source packet, article brief, campaign plan, decision memo, or report?
```

2. Run a fast scan:

```text
Call gpt-researcher quick_search with 2-3 versions of the query. Summarize the
terrain, obvious sources, and whether deep research is justified.
```

3. Run deep research:

```text
Call gpt-researcher deep_research with a narrow query. Ask for objective tone.
Keep the research_id.
```

4. Pull context and sources:

```text
Call get_research_context and get_research_sources. Separate findings,
confidence, source URLs, and gaps.
```

5. Synthesize for the destination:

```text
For articles: convert to a content brief.
For social: convert to topic angles and evidence.
For ads: convert to offer angles, objections, and proof points.
For email: convert to segment-specific send ideas.
For education: convert to learning objectives, must-cover concepts, and review
notes.
For metrics: convert to possible causes and recommended tests.
```

6. Hand off:

```text
Pass the research_context into Sidecar, Katailyst playbooks, specialist writers,
rubrics, or a human review queue.
```

## Operating Guardrails

- Start with `quick_search`; deep research costs more and takes longer.
- Completed `research_id` metadata is durable when `RESEARCH_RUN_STORE_PATH` and
  `OUTPUTS_DIR` point at persistent storage. In-flight runs interrupted by a
  restart are marked `failed` with `interrupted_by_restart`; they are not
  resumed automatically.
- Use REST for deterministic server calls, MCP for agents, and UI for humans.
- Keep HLT/Katailyst composition in the caller or registry, not in the public
  GPT Researcher browser UI.
- Do not expose `API_AUTH_KEY`, `MCP_AUTH_TOKEN`, `GPTR_MCP_TOKEN`, or
  Katailyst tokens in browser source, public env, screenshots, docs, or logs.
- For medical, legal, financial, or compliance-sensitive outputs, use GPT
  Researcher as evidence gathering, then require domain review.
- Expect cold starts and long-running deep research. Agent callers should handle
  60-240 second waits for deep flows.

## Failure Modes

| Symptom | Likely cause | First check |
| --- | --- | --- |
| REST returns `401` | Missing or wrong `X-API-Key` | Confirm `API_AUTH_KEY` in the caller runtime |
| MCP returns `401` | Missing or wrong bearer token | Confirm `GPTR_MCP_TOKEN` in local agent env |
| MCP session errors | Missing MCP session id after initialize | Re-run initialize and reuse `mcp-session-id` |
| UI loads but research fails | API auth/WebSocket token path or backend runtime error | Run `scripts/smoke_websocket_ui.py` |
| Scope badge says `Needs config` | Missing server-side MCP/Firecrawl env | Check `/api/hlt/readiness` through the UI proxy |
| Scope selected but not used | Backend degraded the scope cleanly | Inspect `hlt_scope_status` in the WebSocket log |
| Deep research is slow | Expected for broad queries or cold start | Narrow the query; use quick search first |
| Weak sources | Query too broad or retriever underfilled | Add domains, narrow geography/date/persona, or retry |
| Report looks alive but logs error | Check Railway logs and `outputs/*.json` handling | Run logging tests before redeploy |

## Smoke Commands

API:

```bash
curl -fsS https://gpt-researcher-api-production.up.railway.app/health

curl -i -sS -X POST https://gpt-researcher-api-production.up.railway.app/api/quick_search \
  -H "Content-Type: application/json" \
  -d '{"query":"NCLEX-RN pass rate 2026","summary":true}'

curl -sS -X POST https://gpt-researcher-api-production.up.railway.app/api/quick_search \
  -H "X-API-Key: $API_AUTH_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"NCLEX-RN pass rate 2026","summary":true}'
```

MCP:

```bash
curl -fsS https://gpt-researcher-mcp-production.up.railway.app/health

curl -i -sS https://gpt-researcher-mcp-production.up.railway.app/mcp
```

Restart persistence:

```bash
.venv/bin/python scripts/smoke_research_persistence.py
```

UI/WebSocket:

```bash
.venv/bin/python scripts/smoke_websocket_ui.py \
  --ui-url https://gpt-researcher-ui.vercel.app \
  --api-url https://gpt-researcher-api-production.up.railway.app \
  --scope codebase,metrics,firecrawl \
  --allow-degraded-scope
```

## Taking It To The Next Level

Do these in this order:

1. Add Sidecar prompt/tool-routing guidance so Sidecar calls
   `tool:gpt-researcher.mcp` through Katailyst when a workflow needs cited web
   research. This belongs in Sidecar/Katailyst, not this upstream fork.
2. Add saved research packets to Sidecar drafts or MasteryPublishing metadata:
   `research_context`, `source_urls`, `research_date`, `research_id`, and
   `confidence_notes`.
3. Add freshness gates before publishing: if a content item depends on
   fast-changing facts, require a recent `quick_search` or `deep_research`
   source packet.
4. Add weekly research sweeps as automations for articles, social, ads, and
   email. Start with topic discovery, not automatic publishing.
5. Add cost/latency tags in the caller runtime so GPT Researcher usage can be
   measured by lane and output type.
6. For production restart safety, keep the SQLite run store and generated
   outputs on the same durable Railway volume.

The strategic target is simple: Katailyst decides what capability should run,
GPT Researcher performs external research when it is the right capability,
Sidecar turns the research into content/workflow outputs, and this upstream fork
stays small enough to keep syncing with the community project.
