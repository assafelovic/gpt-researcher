# content-brain — 6-Phase Build Plan

Fork of `assafelovic/gpt-researcher` adapted into a personal research → knowledge → publishing pipeline.

**Upstream remote:** `assafelovic/gpt-researcher` (for rebasing)
**Origin:** `jwj2002/gpt-researcher`
**Local dir:** `~/projects/content-brain`

---

## Architecture

```
                       ┌──────────────────┐
     Topic  ─────────▶ │   Research Loop  │  (forked gpt-researcher)
                       └────────┬─────────┘
                                │  synthesized markdown + sources
                                ▼
                   ~/brain/research/*.md      ◀── Basic Memory MCP
                                │                  (queryable via Claude)
                                ▼
                     ┌─────────────────────┐
                     │  Approval Queue     │  (FastAPI + React)
                     │  draft → approve    │
                     └──────────┬──────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              LinkedIn       Blog      Personal site
              (Typefully)  (git push)  (git push)
```

---

## Phase 1 — Foundation

**Goal:** Clean fork, runs locally, produces a research report end-to-end.

**Tasks:**
- Remove sprawl — delete `multi_agents_ag2/`, `mcp-server/` (don't need these)
- Keep — `gpt_researcher/`, `backend/`, `multi_agents/`, `frontend/`, `docs/`
- Set up `.env` with `OPENAI_API_KEY`, `TAVILY_API_KEY`
- Install deps — `pip install -r requirements.txt` (use venv or uv)
- Smoke test — run one query via CLI, confirm markdown output
- Commit the cleanup — `chore: remove unused parallel agent implementations`

**Exit criteria:**
- [ ] `python cli.py "<some topic>"` produces a markdown report
- [ ] Repo runs without the deleted directories
- [ ] First commit on the fork

**Files to open first:**
- `gpt_researcher/agent.py` — the orchestrator
- `gpt_researcher/prompts.py` — where quality lives
- `gpt_researcher/config/variables/default.py` — the knobs
- `backend/server/server.py` — the API surface

---

## Phase 2 — Knowledge Store

**Goal:** Every research output persists to a queryable second brain.

**Tasks:**
- Install Basic Memory — `uv tool install basic-memory` or `pip install basic-memory`
- Point it at `~/brain/` (its default)
- Add post-research hook in the fork — after `write_report()` completes, write to `~/brain/research/{YYYY-MM-DD}-{slug}.md` with YAML frontmatter (topic, sources, date, status: `draft_ready`)
- Connect Basic Memory's MCP server to Claude Desktop — `basic-memory mcp`
- Verify — ask Claude "what have I researched about X?" and get a real answer from the vault

**Exit criteria:**
- [ ] Research auto-stores to `~/brain/research/`
- [ ] Claude Desktop can search + cite notes from the vault
- [ ] Frontmatter includes sources so you can trace back

**Notes:**
- Plain markdown on disk — you can grep, open in any editor, move anywhere
- Basic Memory rebuilds its index from source files anytime (zero lock-in)

---

## Phase 3 — Approval Queue

**Goal:** Research runs → draft lands in a review UI → you approve/edit/reject.

**Tasks:**
- Add `queue` module to the backend (alongside `backend/server/`)
- SQLite table — `(id, topic, style, status, draft_md, sources_json, destination, created_at, scheduled_for)`
- Statuses: `pending → researching → draft_ready → approved → published`
- Routes: `POST /queue` (submit topic), `GET /queue` (list), `GET /queue/{id}`, `PUT /queue/{id}`, `POST /queue/{id}/approve`
- React page — list view, detail/edit view, regenerate button, approve button
- Wire "submit" → kicks off research asynchronously → updates status when done

**Exit criteria:**
- [ ] Submit a topic from the UI, see it move through statuses
- [ ] Edit a draft inline, save changes
- [ ] Approve a draft (for now, approval just sets status — publishing comes in Phase 5)

**Decision needed before starting:**
- SQLite or Postgres? → Start SQLite, upgrade later if needed.
- React or reuse the existing Next.js frontend? → Reuse if possible (less code), new if the queue UI doesn't fit.

---

## Phase 4 — Style Presets

**Goal:** Same topic → different post formats per destination.

**Tasks:**
- Create `gpt_researcher/styles/` module
- Write 3–5 preset prompt templates (each is a complete rewrite of `generate_report_prompt`):
  - `linkedin_data_driven` — 200 words, hook + 3 data points + CTA
  - `linkedin_contrarian` — 180 words, strong claim + evidence + reframe
  - `blog_deep_dive` — 1500 words, essay with subheadings
  - `executive_brief` — 180 words, headline + 3 bullets + implication
  - `brain_note` — long-form, for future-you, no audience
- Add `style` field to queue — chosen at submit time
- Queue routes accept `style` param, pass through to research call
- Regenerate button supports changing style without new research (reuse context, re-render)

**Exit criteria:**
- [ ] Same topic, 3+ distinct outputs, each matches its destination's shape
- [ ] Style selector in the submit UI
- [ ] Regenerate-with-different-style works without re-searching

**Decision needed:**
- Write these styles before you start. Draft 3 example posts by hand in each style — if you can't, the style isn't real yet.

---

## Phase 5 — Publishing Adapters

**Goal:** One click from approved draft to live post on any destination.

**Tasks:**
- Adapter interface — `publish(draft) -> {url, published_at}`
- **LinkedIn adapter** — Typefully API (~$15/mo) — one HTTP call. Do NOT try to hit LinkedIn directly.
- **Blog adapter** — writes markdown to your static site's `content/posts/` dir in a separate git repo, commits, pushes. CI deploys.
- **Personal site adapter** — same pattern as blog, different repo.
- **Second-brain-only adapter** — no-op (report already stored in Phase 2).
- Queue stores `destination` on the draft. Approve button routes to the right adapter.

**Exit criteria:**
- [ ] Approve → publish → live link returned within seconds
- [ ] Works for all three destinations
- [ ] Failed publishes are recoverable (status reverts, error shown)

**Decisions needed before starting:**
- Which blog engine? (Astro, Hugo, Ghost, Jekyll, custom?) — determines adapter shape
- Typefully account created? — prerequisite
- Personal site repo URL? — needed for adapter config

---

## Phase 6 — Quality Upgrade + Chat

**Goal:** Make the output genuinely good. Optional chat UI over the brain.

**Tasks (pick from these as needed):**

**Quality:**
- Port STORM's multi-persona conversation as a new `skills/personas.py` module
  - Generate 3–5 personas per topic (expert, contrarian, novice, practitioner)
  - Simulate writer↔expert turns grounded in retrieved sources
  - Feed transcript into final draft
- Voice-locking — few-shot layer using your best past posts as style exemplars (store in `~/brain/voice/`)
- Regenerate-with-notes — text box for critique, second-pass rewrite incorporating feedback
- Prompt evals — add a small pytest suite that runs known topics through the pipeline, scores output against rubric

**Chat (optional):**
- Already works for free via Claude Desktop + Basic Memory MCP — use that first
- Build dedicated chat UI only if Claude Desktop falls short

**Exit criteria (quality):**
- [ ] Outputs are distinctly better than Phase 4 baseline (subjectively and by eval scores)
- [ ] Voice matches your past writing on blind A/B comparison

---

## What We're NOT Building

- Own scheduler — Typefully / Buffer handle this
- Trending-topics crawler — you provide the topics
- Mobile app
- Agent framework (LangGraph, CrewAI) unless a Phase 6 problem demands it
- Custom vector DB — Basic Memory and its FastEmbed index are enough at personal scale

## Rebase Strategy

Upstream is active — rebase periodically to absorb research-engine improvements:

```bash
git fetch upstream
git rebase upstream/main         # upstream's default branch
# Resolve conflicts in prompts.py and agent.py (highest-change files)
```

Before each rebase, ensure your customizations live in clearly-separated files (`gpt_researcher/styles/`, `queue/`, etc.) to minimize conflicts.

## Open Decisions

Track these as they come up:

- [ ] Blog engine (Phase 5 blocker)
- [ ] Personal site framework (Phase 5 blocker)
- [ ] SQLite vs Postgres for queue (Phase 3 — default SQLite)
- [ ] React frontend approach — reuse gpt-researcher's Next.js app or add new (Phase 3)
- [ ] First 3–5 styles content (Phase 4 blocker — decide before writing prompts)
- [ ] Typefully vs Buffer (Phase 5)

## Sequencing Discipline

Ship each phase before starting the next. If Phase 2 alone turns out to be enough tool for your actual needs, that's a valid stopping point. Don't build Phase 5 before Phase 3 is working daily.
