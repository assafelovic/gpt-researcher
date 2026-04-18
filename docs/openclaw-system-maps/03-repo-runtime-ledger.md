# 03-repo-runtime-ledger

> Concrete ledger of major repos, live surfaces, agent/runtime inventory, and Axon rollout expectations.

## Operating rule
- start in Katailyst for ecosystem orientation and capability discovery
- use Axon next for repo-level comprehension, impact analysis, and cleanup work
- do not treat Axon output as a substitute for reading the actual files around a change
- make Axon presence explicit in repo docs, MCP/config surfaces, and cleanup planning wherever it is useful

## Repo ledger

### Katailyst
- repo: `Awhitter/katailyst`
- live: `https://www.katailyst.com`
- mcp: `https://www.katailyst.com/mcp`
- axon: strongest current pilot, with established Axon-first repo-comprehension doctrine and local index already in use
- role: capability canon, registry, orchestration layer
- note: deeper surfaces are auth-protected in public verification

### sidecar-system
- repo: `Awhitter/sidecar-system`
- live: `https://sidecar-system.vercel.app`
- alt live: `https://sidecar-system-work.vercel.app`
- axon: should be standardized as a default repo-comprehension layer and reflected in root agent docs
- role: upstream article and destination orchestration

### MasteryPublishing
- repo: `Awhitter/MasteryPublishing`
- public lane: `https://hltmastery.com/nursing/resources`
- direct alias: `https://v0-next-js-content-engine.vercel.app`
- axon: should be part of the repo-entry pattern so agents can map publishing contracts, route ownership, and refactor impact faster
- role: canonical structured content engine

### Framer and HLTMastery shell
- public site: `https://hltmastery.com`
- key lane: `https://hltmastery.com/nursing/nclex-blog`
- role: shell, nav, footer, landing pages, and legacy public lanes

### Multimedia Mastery
- repo: `Awhitter/Multimedia4Mastery`
- live: `https://multimediamastery.vercel.app`
- axon: should be included in the repo-root guidance and MCP posture as the media lane is hardened
- role: media generation and workflow lane
- public verification note: currently redirects to login

### Content Creator Studio
- repo: `Awhitter/content-creator-studio`
- live: `https://content-creator-studio-lovat.vercel.app`
- axon: should be present if this remains an active coding surface, especially where it overlaps with sidecar-system and publishing lanes
- role: adjacent content workbench frontend

### Agent Canvas
- repo: `Awhitter/Agent-Canvas-`
- live: `https://agent-coordination-canvas.replit.app/`
- axon: should be added to the same cross-repo repo-entry doctrine so coordination-plane code is easier to traverse and maintain
- role: coordination and agent canvas surface

### Evidence-Based Business
- repo: `Awhitter/Evidence-Based-Business`
- live: `https://clean-ebb.vercel.app`
- alt live: `https://build-measure-learn.vercel.app`
- project id: `prj_HfvAywsc0pUBM3PSqs0SH3Fl9Eia`
- axon: should be standardized here too so warehouse, analytics, and decision-support contracts can be inspected quickly before cleanup or schema changes
- role: measurement, warehouse, and decision-support layer
- intended purpose: centralize meaningful slices of app usage, financials, conversion, article and landing-page performance, and other business metrics in a way agents can query and use
- strategic note: this should be treated as closer to core infrastructure than a sidecar because it is meant to feed decision-grade data into agents and downstream surfaces

## Active agent ledger

### Victoria
- runtime: Render and OpenClaw
- service: `openclaw`
- role: primary orchestrator

### Julius
- runtime: Render and OpenClaw
- service: `openclaw-justin`
- role: Justin-focused operator

### Lila
- runtime: Render and OpenClaw
- service: `openclaw-marketing`
- role: marketing operator

### Secondary agent surfaces
- Claude Code SDK agent
- parent and sub-agent canvas patterns

## MasteryPublishing implementation references
Pulled from `PROJECT_RECAP_AND_ELEVATION_PLAN.md` and related docs:
- `app/resources/page.tsx`
- `app/resources/[product]/page.tsx`
- `app/resources/[product]/[slug]/page.tsx`
- `app/resources/search/page.tsx`
- `app/api/publish/route.ts`
- `app/api/revalidate/route.ts`
- `components/layout/navbar.tsx`
- `components/layout/footer.tsx`
- `lib/data/articles.ts`
- `lib/data/settings.ts`

## Axon rollout and cleanup notes
- Axon should appear as a normal repo-comprehension layer across the major active repos, not as a hidden specialist trick
- each major repo should eventually expose the same compact repo-entry pattern: what the repo is, related repos and live surfaces, source-of-truth boundaries, Axon-first comprehension, available MCP surfaces, and where to route work if it belongs elsewhere
- current highest-priority rollout set: Katailyst, Agent-Canvas-, sidecar-system, MasteryPublishing, Multimedia4Mastery, and Evidence-Based-Business
- secondary set: content-creator-studio, katailyst-engage, Ecosystem-map, and katailyst-brand-design-lab
- repo cleanup should use Axon for structure discovery, symbol context, impact checks, and dead-code review before larger edits or archive decisions
- repo-local llms outputs should be generated, not hand-maintained
- public verification and private repo introspection should be labeled distinctly
