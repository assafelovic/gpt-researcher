# HLT Ecosystem Index for Agents

> Official cross-repo front door for AI agents working anywhere in the HLT ecosystem. Read this file first. It explains what repos exist, what they are for, where they live, what URLs they own, what core shapes and contracts matter, which systems are canonical, and how to navigate the ecosystem without acting like the current repo is the whole world.

This file is intended to be copied or generated into every major repo as `llms.txt`.

## Jump to

Short index for agents who don't need to read 700 lines sequentially. Every section below is reachable by anchor.

- [Read this first](#read-this-first) — seven rules, read in full
- [Standard working method](#standard-working-method) — eight-step startup
- [Big-picture vision](#big-picture-vision) — strategic intent, quality posture, business focus, content ambition, research posture, centerpieces
- [Katailyst-first rule](#katailyst-first-rule) — discovery pattern + standard startup sequence
- [Axon rule](#axon-rule) — when and how to use Axon for repo comprehension
- [Key Katailyst entities](#key-katailyst-entities) — canonical refs to load first (KBs, skills, tools, playbooks, rubrics, hubs)
- [Official canon docs](#official-canon-docs)
- [Current truths and decisions](#current-truths-and-decisions)
- [Repo inventory](#repo-inventory) — 15 repos, roles, inspect-first files
- [Active agent and runtime inventory](#active-agent-and-runtime-inventory) — Victoria, Julius, Lila + fleet
- [Current focus — Framer + Next.js + article sidecar flow](#current-focus-framer--nextjs--article-sidecar-flow)
- [Cross-repo check matrix](#cross-repo-check-matrix)
- [HLTMastery, Framer, and proxy boundary](#hltmastery-framer-and-proxy-boundary)
- [Core content and publishing shapes](#core-content-and-publishing-shapes) — ArticleV2, lifecycle, SEO, destinations
- [Cloudinary system summary](#cloudinary-system-summary)
- [Corporate data and CMS reality](#corporate-data-and-cms-reality)
- [Near-term priorities](#near-term-priorities-that-matter-right-now)
- [Key rules agents must follow](#key-rules-that-agents-must-follow)
- [Companion files](#companion-files)
- [Sync and update model](#sync-and-update-model)

## Key Katailyst entities

Load these via MCP `get_entity` or `registry_artifact_body` before doing serious work. Each `type:code` is a canonical registry ref; names stable across revisions. Full catalog of 1,663 entities is discoverable via `registry_capabilities` + `discover`.

### Operating canon
- `kb:katailyst-vault-access-pattern` — canonical secrets access. Read BEFORE hunting in env files or vault backups. Lists all 128 active secrets + their `secret_key` names.
- `kb:hlt-brand-voice-hlt-mastery-communication-guide` — live brand voice standard for customer-facing and editorial content.
- `kb:hlt-brand-voice-fnp` — FNP product voice overlay (pairs with content-patterns-nursing).
- `kb:content-patterns-nursing` — Nursing voice guide. Load for any nursing-scoped output.
- `kb:beliefs-operating-constitution` — foundational operating document: vision, philosophy, anti-patterns, build-vs-orchestrate posture.
- `kb:cloudinary-folder-architecture` — canonical Cloudinary folder tree + naming rules.
- `kb:cloudinary-integration-guide` — Cloudinary API patterns + transformations.
- `kb:registry-design-patterns` — how registry entities should be structured.
- `kb:langfuse-tracing-hlt` — trace tag schema (includes mandatory `paperclip_run_id`).

### Hubs (domain front doors — `traverse` to expand)
- `hub:hub-research` — research lane (firecrawl, brave, tavily, perplexity, gpt-researcher).
- `hub:hub-social` — 34 social channels + playbooks + schemas.
- `hub:hub-email` — email marketing + Marketo.
- `hub:hub-multimedia` — image/video/audio generation.
- `hub:hub-registry` — registry self-reference + canonical operating KBs.
- `hub:hub-education` — education content + QBank tools.
- `hub:hub-nclex` — NCLEX program hub (217 linked entities).

### Playbooks + prompts
- `playbook:make-article` — canonical article flow.
- `playbook:make-social` — canonical social flow.
- `playbook:upgrade-screen-ab-test` — paywall / upgrade-screen A/B framework.
- `prompt:hlt-prompt-direct-response-copywriter` — AIDA/PAS/BAB direct-response framework.
- `prompt:social-post-v1` — platform-aware social drafting.

### Rubrics
- `rubric:article-quality-v1` — article evaluation gate.
- `rubric:content-quality` — generic content evaluation fallback.
- `rubric:engagement-v1` — engagement-focused eval.
- `rubric:tool-reliability` — executable-tool health check.

### Tools callable via `tool_execute`
- `tool:cloudinary.transform` — URL-based image transforms (no auth, public delivery).
- `tool:cloudinary.upload` — signed uploads (vault `cloudinary/api-secret`).
- `tool:meta-ads.insights` — Meta Graph insights (vault `meta/ads/access-token`, query-param auth; http_multi_action executor pending on MCP side).
- `tool:manus.agent` — multi-step Manus agent runner (vault `manus/api-key`).
- `tool:elevenlabs.voice` — TTS (vault `elevenlabs/api-key`).
- `tool:gpt-researcher.quick-search` — cited web research (live at `gpt-researcher-production-2b53.up.railway.app`).
- `tool:hlt-metabase-readonly` — HLT warehouse reads (50K+ items).
- `tool:publish.email` — Resend transactional email (vault `resend/api-key`).
- `tool:marketo` — Marketo CRUD (vault `marketo/client-id` + `marketo/client-secret`).
- `tool:v0.model_generate` / `tool:v0.platform_scaffold` — v0 code generation (vault `v0/api-key`).

### Governance + lint
- `lint_ruleset:registry-graph-governance` — registry graph health checks.
- `lint_rule:no-hollow-published` — blocks empty-shelled `published` entities.
- `lint_rule:cascade-warning-on-archive` — flags orphan-making archival.
- `lint_rule:deprecated-needs-supersedes` — deprecation requires migration target.
- `lint_rule:cross-type-pair-integrity` — content_type/recipe duality rules.

## Read this first

- This ecosystem spans multiple repos. Do not assume the current repo contains the whole system.
- Everything starts with **Katailyst**. Use Katailyst first for capability discovery, ecosystem orientation, and cross-system routing.
- Use **Axon second** for repo comprehension, critical path analysis, impact analysis, and finding the real files and symbols that matter.
- If your task touches HLTMastery public routes, Next.js publishing, Framer pages, media generation, article workflows, or cross-system data flow, assume cross-repo inspection is required.
- Verify **live/runtime truth** before making architectural claims.
- Prefer a few official giant docs over stale note sprawl.
- Do not confuse shell ownership, public route ownership, content ownership, and media ownership. They are separate questions.

## Standard working method

1. Read this `llms.txt`
2. Read `AGENTS.md`
3. Read `cloud.md` if present
4. Use Katailyst MCP for orientation
5. Use Axon for repo comprehension
6. Check relevant sibling repos
7. Verify live URLs and runtime reality
8. Then edit, document, or operate

## Big-picture vision

This ecosystem exists to give AI agents a large, high-quality arsenal of building blocks, tools, knowledge, schemas, and integration surfaces that can be used in the right circumstance across many years, many models, and many platforms.

The goal is not one rigid workflow.
The goal is a smart adaptive system.

### Core strategic intent
- grow HLT over the next several months, especially in test prep and recruiting
- build an AI operating system that can continuously absorb new tools and capabilities as they appear
- make those capabilities usable across many platforms through Katailyst and related surfaces
- let agents operate with judgment, decomposition, critical thinking, and context rather than forcing every request into one pre-scripted playbook
- keep the system coherent, inspectable, repairable, and high quality even as it scales to thousands of entries and many people on the team

### What Katailyst should become for agents
Katailyst should act like a capability armory and orchestration layer.
Agents should bring their real objective and current situation, and the MCP/registry layer should help decompose that objective into smaller parts, search for the right capability regions, send sub-agents to inspect those regions, and bring back the best building blocks for composition.

That means the system should support workflows like:
1. agent brings objective and context
2. system decomposes the objective into 2-10 subproblems depending on complexity
3. vector/discovery search finds relevant regions, entities, tools, and knowledge blocks
4. sub-agents inspect those regions and traverse locally
5. sub-agents return the best components or observations
6. the main agent composes the result
7. the MCP and registry layer tracks what happened so the burden is not entirely on the agent to self-track

### Quality posture
- schemas should be strict and high quality
- agents should be encouraged to think critically, not mechanically
- agents may use 50%, 80%, or 100% of a capability if that is the right fit
- problems, drift, stale knowledge, and broken surfaces should be flagged rather than silently worked around
- hubs and front doors are useful, but the system should not rely only on shallow hub navigation. Deep search, region finding, and graph traversal matter.

### Business focus right now
- test prep growth
- recruiting growth
- marketing visibility and awareness
- scaling high-value educational resources and articles
- especially building broad topical coverage, including niche topics that are underserved but valuable

### Content ambition
A major near-term goal is an NCLEX encyclopedia or NCLEX OPedia style system with hundreds of articles across high-value topics, including the niche topics competitors miss. This should be informed by:
- search demand
- audience language and forum discussions
- product data
- question-bank and explanation data where appropriate
- what the best content operators in the world are doing right now

### Research posture
Agents should use tools like Firecrawl, Tavily, and forum or customer research to understand what the audience actually cares about, how they speak, and what topics deserve coverage. This should not rely only on the user manually providing topics.

### Benchmarking posture
Study strong operators and apply lessons to the system. Follow and analyze examples like:
- Replit
- Vercel
- New York Times
- other best-in-class resource and article creators

### System centerpieces
- **Katailyst** is the centerpiece of skills, capabilities, schema, and orchestration
- **Agent Canvas** is the centerpiece of agents, plans, and coordination surfaces
- **sidecars** are use-case launch surfaces, not hard limitations; they should still be able to call broad capability surfaces
- **Multimedia Mastery + Cloudinary** are central to the multimedia future
- **Evidence-Based Business** should increasingly hold important data and measurement layers

## Katailyst-first rule

Use Katailyst before guessing at capabilities or inventing workflows.

### Standard startup pattern
1. `registry_capabilities`
2. `registry_session`
3. `registry_agent_context`
4. `discover / get_entity / traverse`
5. `tool_describe`
6. `tool_execute`

### Why this matters
Katailyst is the capability canon for this ecosystem. It exposes tools, prompts, entities, and integration surfaces that agents should reuse instead of re-inventing locally.

### Axon-grounded repo facts
- `lib/mcp/handlers/registry-read/capabilities.ts` contains the registry capabilities handler
- `lib/mcp/tool-definitions-read.ts` registers discovery and read tools like `discover`
- `lib/mcp/tool-definitions-execution.ts` registers execution surfaces like `tool.search`, `tool.describe`, and `tool.execute`
- `lib/docs/llms-index.ts` already contains llms rendering logic, including MCP surface rendering functions
- `deploy/openclaw-katailyst-plugin/index.ts` includes plugin-side prompt nudges and registry defaults

### Confirmed capability lanes
- research and web
- Firecrawl search, scrape, map, crawl, extract, batch-scrape
- Firecrawl browser and agent escalation
- Cloudinary tools
- AgentMail send and receive
- publish.email
- deploy and dev surfaces
- analytics and integration surfaces

## Axon rule

Use Axon for repo comprehension after Katailyst orientation.

### Axon is for
- symbol-level understanding
- impact analysis
- critical pathways
- identifying important files and modules
- understanding what calls what

### Axon is not enough by itself for
- source-of-truth ownership
- strategic role decisions
- public and live route ownership
- runtime reality

## Official canon docs

These are the intended top-level canonical docs in Obsidian:
- `00-START-HERE`
- `01-ecosystem-atlas-master`
- `02-content-media-publishing-atlas`
- `03-repo-runtime-ledger`
- `04-integration-schema-reference`
- `05-llms-ecosystem-master`

Use these before digging through older overlapping notes.

## Current truths and decisions

These are the current truths agents should operate from unless a newer verified source overrides them:

- Katailyst is the centerpiece of skills, capabilities, schema, registry, and orchestration
- Agent Canvas is the centerpiece of agent and plan coordination thinking
- sidecar-system is an upstream workflow and publishing-orchestration surface, not just a local UI shell
- MasteryPublishing is the canonical structured `/resources/**` content destination
- Framer is a first-class shell, landing-page, navigation, branded public-experience, and legacy or public content surface
- Cloudflare proxy stitches public HLTMastery routes across multiple underlying systems
- Cloudinary is the intended system of record for media assets and derivatives
- Multimedia Mastery is the intended multimedia generation and media-workflow lane
- the Next.js publishing page and HLTMastery route alignment are among the most important near-term live surfaces
- sidecar should remain able to publish to both Framer and the structured content lane where that is strategically right
- agents should always use Katailyst first and Axon second when operating in this ecosystem
- the public domain is not the same thing as the canonical system boundary
- shell ownership, route ownership, content ownership, and media ownership are separate questions and should not be collapsed together casually

## Repo inventory

For each major repo, this document should answer:
- what the repo is
- what it is for
- how it fits the broader system
- what surfaces other agents interact with
- what URLs and routes matter
- what shapes or contracts matter operationally
- where to inspect first

### Katailyst
- **Repo:** `Awhitter/katailyst`
- **GitHub:** `https://github.com/Awhitter/katailyst`
- **Live:** `https://www.katailyst.com`
- **MCP:** `https://www.katailyst.com/mcp`
- **Last verified:** 2026-04-15
- **Role:** capability canon, registry, orchestration layer, MCP surface
- **Main purpose:** the control plane and armory repo for Catalyst and Katailyst, with Supabase-canonical atomic units, discovery APIs, CMS and operator surfaces, portability mirrors, and export layers for downstream runtimes
- **Main surfaces other agents interact with:** `/mcp`, registry and discovery tools, prompts, resources, toolsets, llms docs surfaces (`/.well-known/llms.txt`, `/llms.txt`, `/llms-full.txt`, `/llm.txt`), docs like `docs/VISION.md`, `docs/RULES.md`, and `docs/QUICK_START_AGENTS.md`
- **Key shapes and contracts:** registry entities, tool refs, integration contracts, capability packets, runtime context, prompts, resources, toolsets
- **Inspect first:** `lib/docs/llms-index.ts`, `lib/mcp/handlers/registry-read/capabilities.ts`, `lib/mcp/tool-definitions-read.ts`, `lib/mcp/tool-definitions-execution.ts`
- **Axon-grounded pathways:**
  - `lib/docs/llms-index.ts::renderMcpSurfaceSection` builds the MCP section used in Katailyst llms docs and is called by `renderLlmsTxt`
  - `lib/docs/llms-index.ts::renderLlmsTxt` is the main compact llms renderer and is called by `buildLlmsOutputTargets`
  - `lib/docs/llms-index.ts::buildLlmsOutputTargets` is the core output builder for `llms.txt`, `llms-full.txt`, and compatibility outputs
  - `scripts/ops/generate_llms_docs_index.ts::main` is the generation script entrypoint for Katailyst llms docs
  - `lib/mcp/session-summary.ts::buildMcpQuickstartPrompt` contributes the MCP quickstart summary pattern
  - `lib/mcp/playground-guides.ts::docsAndVaultSnippet` explicitly points clients at `/.well-known/llms.txt`, `/llms.txt`, and `/llms-full.txt`

### sidecar-system
- **Repo:** `Awhitter/sidecar-system`
- **GitHub:** `https://github.com/Awhitter/sidecar-system`
- **Local:** `/Users/alecwhitters/Downloads/sidecar-system`
- **Live:** `https://sidecar-system.vercel.app`
- **Alt live:** `https://sidecar-system-work.vercel.app`
- **Last verified:** 2026-04-15
- **Role:** upstream workflow and control plane for content and destination orchestration
- **Main purpose:** domain-specific AI content interfaces powered by the Katailyst MCP registry, with specialized sidecars for articles, social, email, analytics, education, multimedia, and related workflows
- **Main surfaces other agents interact with:** article sidecars, `domains/<name>/sidecar-config.ts`, MCP bridge, destination publishing tools, Framer integration routes, content-engine projection routes, chat and runtime workflows
- **Key shapes and contracts:** `ArticleV2`, destination publish payloads, Framer projection shape, content engine publish shape
- **Inspect first:** `app/(apps)/chat/tools/contentEnginePublish.ts`, `app/(apps)/chat/tools/publishToDestinations.ts`, `lib/publish/content-engine.ts`, `lib/framer/resources.ts`, `lib/content-engine/projection.ts`, `lib/framer/projections.ts`
- **Axon-grounded pathways:**
  - Framer publish flow is centered on `app/api/framer/publish/route.ts` to `lib/framer/resources.ts::requestPublish`
  - `requestPublish` is called by both the explicit API route and `framerRequestPublishToolFactory`, and internally uses `withFramerClient`, `isPublishPermissionError`, and `lib/sidecar/events/phase-bus.ts::publish`
  - Framer resource upsert flow is centered on `app/api/framer/resources/route.ts` to `lib/framer/resources.ts::upsertDraftResource`
  - `upsertDraftResource` is called by both the explicit API route and `framerUpsertResourceToolFactory`, and internally depends on `projectArticleToFramerItem`, `findResourcesCollection`, `buildDeepLink`, `uploadExternalImages`, and `withFramerRetry`
  - `projectArticleToFramerItem` in `lib/framer/projections.ts` is the core ArticleV2 to Framer payload mapping layer and depends on block rendering, enum resolution, field setting, and schema cache reads
  - `ArticleV2` is defined in `lib/framer/types.ts` and imported across block rendering, client access, enums, image upload, projections, resources, schema cache, and vault integration

### MasteryPublishing
- **Repo:** `Awhitter/MasteryPublishing`
- **GitHub:** `https://github.com/Awhitter/MasteryPublishing`
- **Local:** `/Users/alecwhitters/Downloads/MasteryPublishing`
- **Legacy live alias:** `https://v0-next-js-content-engine.vercel.app`
- **Public route family:** `https://hltmastery.com/nursing/resources`
- **Last verified:** 2026-04-15
- **Role:** canonical structured `/resources/**` content engine
- **Main purpose:** the HLT study-resources publishing app and content display layer, rendering the public `/resources/**` library, serving product-specific hubs and article pages, reading from Supabase, and accepting article publishes from the Katailyst pipeline
- **Main surfaces other agents interact with:** `/resources`, `/resources/[product]`, `/resources/[product]/[slug]`, `/resources/search`, `/admin`, `POST /api/publish`, `POST /api/revalidate`, `GET|POST /api/admin/settings`, Supabase-backed product, topic, author, article, and settings data layer
- **Key shapes and contracts:** article publish payload, product and article relations, topic and author relations, settings shapes, revalidation contract
- **Inspect first:** `app/api/publish/route.ts`, `app/resources/page.tsx`, `app/resources/[product]/page.tsx`, `app/resources/[product]/[slug]/page.tsx`, `lib/data/articles.ts`, `lib/data/settings.ts`
- **Axon-grounded pathways:**
  - publish entrypoint is centered on `app/api/publish/route.ts::POST`
  - resources landing flow is centered on `app/resources/page.tsx::ResourcesPage` to `getResourcesPageSettings` and `getProducts`
  - article detail flow is centered on `app/resources/[product]/[slug]/page.tsx::ArticlePage` to `getArticleBySlug`, `getArticlePageSettings`, and `getProductBySlug`
  - admin flow is centered on `app/admin/page.tsx::AdminPage` to `getAllSettings`, `getProducts`, and `getArticles`
  - product and article data access is concentrated in `lib/data/articles.ts`, especially `getArticles`, `getArticleBySlug`, `getProducts`, and `getProductBySlug`
  - settings access is concentrated in `lib/data/settings.ts`, especially `getResourcesPageSettings`, `getArticlePageSettings`, and `getAllSettings`

### Multimedia Mastery
- **Repo or product:** `Awhitter/Multimedia4Mastery` and local multimedia-mastery-core naming family
- **Local:** `/Users/alecwhitters/Downloads/multimedia-mastery-core`
- **Live:** `https://multimediamastery.vercel.app`
- **Last verified:** 2026-04-15
- **Role:** media-native production lane
- **Main purpose:** a media hub and studio that exposes a canonical media tool surface (`/api/media/v1/*`) and a human editor UI (`/studio`, `/m/[moduleId]`) for image, audio, video, upload, and health workflows
- **Main surfaces other agents interact with:** `/api/media/v1/*`, `/studio`, `/m/[moduleId]`, media contracts in `docs/api/MEDIA_TOOL_CONTRACT.md`
- **Key shapes and contracts:** canonical media result shape including `mediaType`, `operation`, `provider`, `asset.url`, `asset.storageId`, dimensions, metadata, `editUrl`, and trace info
- **Inspect first:** `apps/studio/lib/media/cloudinary.ts`, `apps/studio/app/api/media/v1/assets/upload/route.ts`, `apps/studio/app/api/media/v1/image/edit/route.ts`, `apps/studio/app/api/media/v1/image/refine/route.ts`
- **Axon-grounded pathways:**
  - Cloudinary upload logic is anchored in `apps/studio/lib/media/cloudinary.ts::uploadToCloudinary`
  - `uploadToCloudinary` is called by asset upload, audio music generate, audio music status, audio synthesize, video animate, and image-provider helpers in `fal-image.ts` and `gemini-image.ts`
  - `uploadToCloudinary` depends on `requireCloudinaryEnv`, `generatePublicId`, `buildSignature`, `getRemoteSize`, `uploadChunked`, and `buildMediaTags`
  - asset upload API is centered on `apps/studio/app/api/media/v1/assets/upload/route.ts::POST`
  - image edit flow is centered on `apps/studio/app/api/media/v1/image/edit/route.ts::POST`
  - image refine flow is centered on `apps/studio/app/api/media/v1/image/refine/route.ts::POST`

### Content Creator Studio
- **Repo:** `Awhitter/content-creator-studio`
- **GitHub:** `https://github.com/Awhitter/content-creator-studio`
- **Live:** `https://content-creator-studio-lovat.vercel.app`
- **Last verified:** 2026-04-15
- **Role:** adjacent content workbench frontend
- **Main purpose:** a lightweight conversational UI for AI-powered content creation, built as a thin frontend over a backend intelligence layer
- **Main surfaces other agents interact with:** conversational wizard and chat UI, session persistence, registry browser, run history, asset editor, backend API bridge

### EduMastery
- **Repo:** `Awhitter/EduMastery`
- **GitHub:** `https://github.com/Awhitter/EduMastery`
- **Live:** `https://ai4mastery-next-6kpgw1zzw-alecs-projects-e88e78a8.vercel.app`
- **Role:** active-adjacent publishing and admin surface
- **Main purpose:** adjacent publishing and admin behavior and inventory continuity

### Agent Canvas
- **Repo:** `Awhitter/Agent-Canvas-`
- **GitHub:** `https://github.com/Awhitter/Agent-Canvas-`
- **Live:** `https://agent-coordination-canvas.replit.app/`
- **Role:** coordination shell, canvas, and parent-child agent concepts
- **Main purpose:** coordination patterns and agent orchestration concepts

### Evidence-Based Business
- **Repo:** `Awhitter/Evidence-Based-Business`
- **GitHub:** `https://github.com/Awhitter/Evidence-Based-Business`
- **Live:** `https://clean-ebb.vercel.app`
- **Alt live:** `https://build-measure-learn.vercel.app`
- **Role:** measurement and feedback layer
- **Main purpose:** analytics, measurement, feedback-loop support, and experiment interpretation

## Active agent and runtime inventory

Always list active resident agents concretely.

### Victoria
- **Type:** standalone operator agent
- **Runtime:** Render and OpenClaw
- **Service:** `openclaw`
- **Role:** primary orchestrator and fleet commander
- **Status:** active

### Julius
- **Type:** standalone operator agent
- **Runtime:** Render and OpenClaw
- **Service:** `openclaw-justin`
- **Role:** operator for Justin Leas
- **Status:** active

### Lila
- **Type:** standalone operator agent
- **Runtime:** Render and OpenClaw
- **Service:** `openclaw-marketing`
- **Role:** strategist and marketing operator
- **Status:** active

### Other important agent surfaces
- Claude Code SDK agent
- parent and sub-agent canvas model

## Current focus: Framer + Next.js + article sidecar flow

This is the current focus and should be easy for every agent to understand.

### The three-system flow
1. **sidecar-system** is the upstream article creation and publishing orchestration surface
2. **MasteryPublishing (Next.js)** is the canonical structured `/resources/**` destination
3. **Framer and HLTMastery shell** are the branded public shell, navigation layer, and legacy or public surface

### How they flow together
- sidecar creates or refines structured article content
- sidecar can publish to the structured content engine and to Framer when strategically appropriate
- MasteryPublishing renders the structured Next.js article lane
- Cloudflare proxy makes the Next.js lane appear inside the HLTMastery public route family
- Framer still owns the public shell, nav, footer, landing pages, and some legacy or public content families

### Short operating rule
If the task touches the current article pipeline, you almost always need to reason across these three together:
- sidecar-system
- MasteryPublishing
- Framer and HLTMastery public shell

## Cross-repo check matrix

| If the task touches... | Check these first |
|---|---|
| capability discovery, agent tooling, MCP, schemas, registry | Katailyst |
| article creation flow, publish orchestration, destination choice | sidecar-system + Katailyst |
| structured `/resources/**` pages, publish API, revalidation, article display | MasteryPublishing + sidecar-system |
| HLTMastery public shell, nav, footer, landing pages, legacy blog or resources | Framer and HLTMastery shell + MasteryPublishing |
| article images, media generation, branded assets, transformations | Multimedia Mastery + Cloudinary |
| recruiting and test-prep content strategy, topic discovery, performance learning | Katailyst + Evidence-Based Business + research lanes |
| agent coordination, plans, multi-agent work | Agent Canvas + Katailyst |
| corporate educational data, QBank explanation context, upstream content inventory | corporate CMS + relevant publishing and content repos |

## HLTMastery, Framer, and proxy boundary

### Verified public site
- `https://hltmastery.com`

### Verified route examples
- `https://hltmastery.com/nursing/resources`
- `https://hltmastery.com/nursing/nclex-blog`

### Architecture summary: two systems, one domain
The public domain is shared across multiple underlying systems.

- `hltmastery.com/nursing/resources/*` is the structured Next.js content lane served from MasteryPublishing through a reverse-proxy layer
- Framer still owns major shell and public-experience surfaces, including homepage, navigation, footer, and legacy or separate content surfaces
- Cloudflare proxying and path rewriting make these systems feel like one domain even when ownership is split underneath

### Boundary model
- **Katailyst** = canon and orchestration truth
- **sidecar-system** = workflow surface and destination chooser
- **MasteryPublishing** = canonical structured resource destination
- **Framer** = shell, landing pages, brand-facing page builder, navigation layer, and still-important public experience surface
- **Cloudflare proxy** = path stitcher, not canon
- **Multimedia Mastery + Cloudinary** = media lane feeding destinations

### Route mapping to keep in mind
| Public route family | Underlying owner | Meaning | Status |
|---|---|---|---|
| `/nursing/resources` | MasteryPublishing via proxy | structured resources hub | live |
| `/nursing/resources/<product>` | MasteryPublishing via proxy | structured product landing | live |
| `/nursing/resources/<product>/<slug>` | MasteryPublishing via proxy | structured article detail | live |
| `/nursing/resources/search` | MasteryPublishing via proxy | structured search lane | live |
| `/nursing/nclex-blog/*` | Framer | legacy or public blog lane | keep for now |
| `/nursing/fnp/resources/*` | Framer | Framer-managed resource lane | separate lane |
| `/`, main nav, footer, shell surfaces | Framer | public shell and brand experience | shell owner |

### Next.js and MasteryPublishing route anatomy
- `app/resources/page.tsx::ResourcesPage` drives the resources hub via `getResourcesPageSettings` and `getProducts`
- `app/resources/[product]/page.tsx::ProductPage` drives per-product landing routes
- `app/resources/[product]/[slug]/page.tsx::ArticlePage` drives article detail routes via `getArticleBySlug`, `getArticlePageSettings`, and `getProductBySlug`
- `app/resources/search/page.tsx` handles search
- `app/sitemap.ts::sitemap` handles sitemap generation using `NEXT_PUBLIC_SITE_URL` and article and product inventory

### Why the HLTMastery route matters so much
The Next.js publishing page and `/nursing/resources/*` route family are one of the most important near-term live surfaces. They need to stay synchronized with HLTMastery expectations around:
- menu and navigation clarity
- logos and branding
- shell integration expectations
- canonical URLs and metadata
- recruiting and future vertical extensibility
- rich HTML and multimedia support

### Current shell truth
Agents should assume the Content Engine does **not** currently own the whole shell.
That means nav, footer, visual chrome, and overall branded public-experience alignment with Framer are real system concerns, not cosmetic afterthoughts.

### Framer rule
Do not blindly copy Framer pages.
Use this model:
- keep **Framer** as an important shell, landing page, navigation, and branded public-experience layer
- keep **MasteryPublishing** as the canonical structured `/resources/**` lane
- keep sidecar able to publish to **both** when that is strategically right
- use projection, synchronization, and coexistence deliberately rather than collapsing the systems together without boundaries

## Core content and publishing shapes

### Article lifecycle at a glance
```text
sidecar article creation
-> contentEnginePublish or publishToDestinations
-> POST /api/publish in MasteryPublishing
-> Supabase article and taxonomy tables
-> Next.js /resources routes
-> Cloudflare proxy path rewrite
-> hltmastery.com/nursing/resources/*
```

### sidecar upstream working shape: `ArticleV2`
Current surfaced fields include:
- `id`
- `headline`
- `slug`
- `product`
- `category`
- `content_type`
- `subheadline`
- `topics`
- `seo`
- `intro_html`
- `body_html`
- `body_blocks`
- `featured_image`
- `author`
- `word_count`
- `reading_time_minutes`
- `status`
- `content_blocks[]`

### sidecar to MasteryPublishing publish shape
Current surfaced fields include:
- `katailyst_id`
- `slug`
- `title`
- `subtitle`
- `body_html`
- `excerpt`
- `hero_image_url`
- `og_image_url`
- `content_type`
- `category`
- `product_slug`
- `author_slug`
- `faq_json`
- `meta_title`
- `meta_description`
- `word_count`
- `reading_time_minutes`
- `status`
- `featured`
- `topic_slugs`

### sidecar publish destinations
Known destination families include:
- `content_engine` to MasteryPublishing and the structured Next.js content lane
- Framer resource upsert to Framer CMS draft and live lane
- Framer publish request to explicit site publish and deploy lane
- `ai4edu` to adjacent publishing lane when enabled
- social, email, and other downstream destinations via orchestration surfaces

### Rendering path for the public site
```text
User requests hltmastery.com/nursing/resources/<product>/<slug>
-> Cloudflare worker intercepts /nursing/resources/*
-> proxies to MasteryPublishing /resources/<product>/<slug>
-> Next.js fetches article and settings from Supabase
-> Cloudflare rewrites internal links to keep /nursing/resources prefix
-> user sees structured content on hltmastery.com
```

### MasteryPublishing canonical publish contract
Required core fields include:
- `katailyst_id`
- `slug`
- `title`
- `product_slug`

Additional important fields include:
- `body_html`
- `body_json`
- `hero_image_url`
- `hero_image_alt`
- `hero_video_url`
- `og_image_url`
- `category`
- `audience_stage`
- `difficulty_level`
- `tags`
- `estimated_value`
- `faq_json`
- `stats_json`
- `steps_json`
- `comparison_json`
- `citations`
- `meta_title`
- `meta_description`
- `canonical_url`
- `noindex`
- `status`
- `published_at`
- `featured`
- `sort_order`
- `word_count`
- `reading_time_minutes`
- `author_slug`
- `topic_slugs`

### SEO and canonicalization rules
- canonical URLs for structured resources should use `https://hltmastery.com/nursing/resources/*`
- `og:url` should use the public HLTMastery domain, not the raw Vercel domain
- sitemap generation should reflect the intended public domain and route family
- article schema and metadata should point at the public canonical route
- coexistence with Framer legacy routes should be deliberate to avoid duplicate-content confusion

## Cloudinary system summary

### Account identity
- **Cloud name:** `HLT Media`
- **Product environment ID:** `c-1e2a3dbe7b0abcf38e49df4f50a4da`

### Useful console links
- Plans: `https://console.cloudinary.com/app/c-1e2a3dbe7b0abcf38e49df4f50a4da/settings/billing/plans`
- Media library: `https://console.cloudinary.com/app/c-1e2a3dbe7b0abcf38e49df4f50a4da/assets/media_library/folders/home?view_mode=list`
- Metadata fields: `https://console.cloudinary.com/app/c-1e2a3dbe7b0abcf38e49df4f50a4da/assets/media_library/metadata_fields`
- Security settings: `https://console.cloudinary.com/app/c-1e2a3dbe7b0abcf38e49df4f50a4da/settings/security`

### What Cloudinary is for
Cloudinary should be treated as the intended system of record for media assets and derivatives across the ecosystem.

### Top-level folder structure
- `articles/`
- `branding/`
- `in-app/`
- `inbox/`
- `multimedia/`
- `products/`
- `samples/`
- `shared/`
- `social/`

### Metadata fields configured
- `status`
- `source`
- `app_id`
- `vertical`
- `asset_type`

### Watermark and branding model
Cloudinary supports overlay-based watermarking and named transformations.
Recommended HLT pattern:
- store logos in `branding/logos/`
- create named transformations such as `t_hlt_watermark`
- use platform-specific branded transformations for social and media derivatives

### Multimedia rule of thumb
- Multimedia Mastery should be the preferred media-generation and media-workflow lane
- Cloudinary should be the preferred storage, derivative, and branding system of record
- direct generation flows that bypass Cloudinary may be expedient, but they are structurally weaker and should not become the default long-term pattern
- article image quality, asset persistence, tagging, and branded delivery are part of the real system, not optional polish

## Corporate data and CMS reality

There is also a major corporate CMS and database outside the current Katailyst ecosystem that matters.

### Corporate CMS posture
- this system houses large amounts of critical company data, including practice-question and educational content inventory
- it is effectively a major upstream data system for corporate apps
- it should be treated cautiously
- current safe posture is primarily read-oriented, with only carefully limited write behavior where explicitly approved and reliable

### Example surface
- `https://cms.hltcorp.com/items/49311/edit`

### QBank and educational explanation relevance
This corporate data includes structures like:
- question stem
- answer choices
- submission flow
- choice-specific rationale
- key takeaway
- longer explanation and teaching content

These explanation surfaces matter because they can inform:
- educational content quality
- article creation
- SEO topic generation
- teaching patterns
- future content adaptation and enrichment

## Near-term priorities that matter right now

### Highest-priority live surface
The Next.js publishing page and HLTMastery route alignment are among the most important immediate execution priorities.

### What that means concretely
- get the Next.js publishing page live and synced properly with HLTMastery and Framer
- clarify services around the Next.js publishing page, menu and navigation needs, logos, and branding
- keep sidecar able to publish to both Framer and the Next.js content lane
- improve HTML handling and richer multimedia capabilities for the new service layer
- support recruiting and future vertical pages, not just one narrow surface
- improve Slack access for resident agents
- use Victoria, Julius, and Lila as real durable agents, not just ephemeral spin-up workers
- strengthen Agent Canvas as the coordination and canvas layer

### Immediate stabilization checklist
- audit current Supabase article inventory, including published, draft, and missing-image states
- fix visible image 404s and remove placeholder image dependencies
- add canonical tags for structured resources on the HLTMastery public domain
- update `og:url` and related metadata to use the public domain instead of raw Vercel URLs
- verify sitemap and robots behavior for `/nursing/resources/*`
- document the publish workflow clearly so agents know when to use which destination

### Media pipeline stabilization
- fix Multimedia Mastery schema or Oracle failures that block image generation
- connect sidecar article workflows to Multimedia Mastery where appropriate
- route article images through Cloudinary as the asset system of record
- use Cloudinary transformations for branding, watermarking, and distribution

### Content and growth priority
- grow test prep and recruiting visibility through broad high-quality resource and article coverage
- push toward an NCLEX OPedia or encyclopedia style content surface
- cover high-value niche topics at scale
- use forums, Firecrawl, Tavily, product data, and educational data to identify the best topics instead of relying only on manually proposed ideas

### Framer coexistence rule
- keep Framer for shell, public experience, and legacy lanes while the structured content lane proves itself
- do not rush migration just for elegance
- measure speed, SEO, workflow quality, and publishing velocity before large-scale sunset decisions

## Key rules that agents must follow

- Do not assume the current repo is the whole system.
- Use Katailyst first.
- Use Axon second.
- Check sibling repos when the task crosses boundaries.
- Prefer official canon docs over scattered notes.
- Do not confuse shell and public route ownership with canonical content ownership.
- Do not perform dangerous publish actions without explicit approval where required.
- Document concrete things, not vague summaries.

## Companion files

### `AGENTS.md`
Should say:
- read `llms.txt` first
- follow repo-local rules after ecosystem orientation

### `cloud.md`
Should say:
- read `llms.txt` first
- this repo participates in a larger ecosystem
- runtime and deployment notes are local overlays, not the whole system map

## Sync and update model

This file should be maintained once and propagated everywhere.

### Current canonical source
- `/Users/alecwhitters/Documents/Obsidian Vault/OpenClaw/System Maps/05-llms-ecosystem-master.md`

### Current sync script
- `/Users/alecwhitters/.openclaw/workspace/system/sync-llms-to-repos.sh`

### Current generated outputs
Each target repo receives:
- `llms.txt`
- `llm.txt`
- `.well-known/llms.txt`

### Recommended implementation pattern
1. keep the master ecosystem source in Obsidian
2. keep small metadata files per repo only if truly needed later
3. generate repo copies automatically rather than hand-editing them
4. have `AGENTS.md` and `cloud.md` point agents to `llms.txt` first
5. later, validate generation in CI so stale copies are caught

### Why generation matters
If this is hand-maintained separately in each repo, it will drift and stop being trusted. The whole point is to have one document to keep excellent and then spread reliably.

## Last verified
- master ecosystem llms draft last updated: 2026-04-15
- many repo and runtime details remain partially verified and should keep improving

## Bottom line

This ecosystem is multi-repo, multi-runtime, multi-surface, and agents must not behave as if each repo is an island. This file exists to stop that failure mode and provide one official cross-repo entrypoint that can be copied into every important repo.
