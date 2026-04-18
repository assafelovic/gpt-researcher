# 04-integration-schema-reference

> Practical contract reference for the current publishing, CMS, proxy, and issue-tracking surfaces.

## Canonical publish contract
From `CANONICAL_CONTENT_CONTRACT.md`:

### Endpoint
- `POST /api/publish`
- auth: `x-api-key` using `KATAILYST_API_KEY`

### Translation helpers
- `product_slug` resolves to `primary_product_id`
- `author_slug` resolves to `author_id`
- `topic_slugs` resolves to `article_topics` junction rows

### Idempotency rule
- upsert on `katailyst_id`
- repeated publishes with the same `katailyst_id` update instead of duplicating

### Important field groups
- identity and routing
- core content
- media
- classification
- relationships
- structured data blocks
- CTA
- SEO
- publishing state
- timestamps

## Content types
Canonical values include:
- `deep-dive`
- `how-to`
- `faq`
- `listicle`
- `exam-overview`
- `qbank-walkthrough`
- `career-guide`
- `study-guide`
- `myth-buster`
- `news-update`
- `comparison`
- `testimonial`
- `resource-roundup`

## CMS reference
From `CMS_WORKFLOW.md`:
- manual content entry happens in Supabase Studio
- `articles` is the main content table
- `article_topics` manages topic links
- products and authors are reference surfaces

## Proxy-aware SEO requirements
From `PROXY_INTEGRATION_PLAN.md`:
- `NEXT_PUBLIC_SITE_URL=https://hltmastery.com/nursing`
- JSON-LD `@id` should use the proxied public route
- sitemap and robots output should use the proxied public route
- metadataBase and OG generation should use the public proxy-aware base

## Link and rewrite risk area
From `PROXY_INTEGRATION_PLAN.md`:
- root-relative `/resources/...` links may get double-prefixed by the worker if rewrite logic is naive
- this needs verification and coordination with Jason
- `?_rsc=` and client-side navigation behavior must be tested through the proxy

## Linear-ready issue themes
From `LINEAR_ISSUES_READY_TO_CREATE.md`:

### P0
- fix SEO metadata URLs for proxy path
- verify and fix double-prefix URL rewriting through Cloudflare proxy
- fix placeholder image 404s

### P1
- upload real hero images for published articles
- decide and implement nav bar strategy for proxied pages
- replace text placeholder logo with real logo

### P2
- test client-side navigation and RSC fetches through proxy
- create `.env.example`
- plan Multimedia Mastery integration for hero images
- coordinate cache strategy with Jason
- align footer styling with Framer site
- sync llms.txt ecosystem docs across repos

## Evidence-Based Business data direction

This system should evolve into the warehouse and view layer for business data that agents can consume.

### Data families Alec wants agents to use
- individual app usage data
- conversion data
- financial data
- article and content performance data
- Framer and other site performance data
- landing-page and publishing performance data

### Desired operating pattern
- store meaningful metric slices, not just raw dumps
- preserve reusable saved metrics and reusable filtered views
- make those slices easy for agents to query and use in decision-making
- support downstream export of charts and metric visuals, potentially through Cloudinary
- support using metric outputs directly in landing pages and reporting surfaces

### Observability architecture direction
- treat Evidence-Based Business as the warehouse and semantic metric layer for business and content observability
- keep raw ingested data separate from curated metric slices and saved business definitions
- let agents query both current snapshots and durable saved metrics
- design chart outputs so they can become reusable assets for reports, landing pages, and content surfaces
- support using the same metric slices across dashboards, agent reasoning, and published visuals

### Recommended layers
1. ingestion layer
   - app analytics
   - financial exports
   - article and landing page performance
   - Framer and other site metrics
   - conversion and funnel data
2. modeled warehouse layer
   - normalized facts and dimensions for apps, content, pages, campaigns, and time periods
3. saved metrics layer
   - named metrics
   - formulas
   - dimensions
   - filters
   - owners
   - refresh rules
4. agent access layer
   - queryable metric slices
   - prewritten summaries
   - chart specifications
   - landing-page-ready metric blocks
5. asset generation layer
   - chart renders saved as reusable assets, potentially via Cloudinary

### Suggested first-class entities
- app
- metric_definition
- metric_snapshot
- metric_slice
- chart_spec
- chart_asset
- content_asset_performance
- page_performance
- funnel_stage
- financial_period

### Practical implication
Evidence-Based Business should be treated as more core than sidecar. It is the place where business and content data should become agent-usable.

### Katailyst integration implication
The warehouse and observability ideas should be added to the existing Katailyst and Supabase-backed system rather than launching a disconnected new system. The goal is to strengthen the armory, not fragment it.

## Immediate engineering notes
- if touching route generation, inspect `app/layout.tsx`, `app/sitemap.ts`, `app/robots.ts`, and `app/resources/[product]/[slug]/page.tsx`
- if touching publish flow, inspect `app/api/publish/route.ts`, `lib/data/articles.ts`, and sidecar publish tooling
- if touching nav or branding, inspect `components/layout/navbar.tsx` and public Framer shell expectations
