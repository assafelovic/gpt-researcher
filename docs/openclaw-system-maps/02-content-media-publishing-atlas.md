# 02-content-media-publishing-atlas

> Canonical map of article flow, publishing flow, media flow, and the Framer versus Next.js split.

## Article lifecycle
```text
sidecar article creation
-> contentEnginePublish or publishToDestinations
-> POST /api/publish in MasteryPublishing
-> Supabase article and taxonomy tables
-> Next.js /resources routes
-> Cloudflare proxy path rewrite
-> hltmastery.com/nursing/resources/*
```

## Current three-system publishing model

### sidecar-system
- upstream article creation and orchestration
- destination routing
- can publish to structured content lane and Framer when appropriate
- should include Axon in its repo-entry guidance so publishing-flow changes can be mapped before edits

### MasteryPublishing
- canonical structured content destination
- renders `/resources`, `/resources/[product]`, `/resources/[product]/[slug]`, and `/resources/search`
- receives publishes through `POST /api/publish`
- should expose Axon as a standard repo-comprehension and impact-analysis layer in root docs

### Framer
- shell, public experience, nav, footer, landing pages
- legacy public lanes remain live
- should not be blindly copied into the structured content engine

## Proxy integration truths
Pulled from `PROXY_INTEGRATION_PLAN.md`:
- Cloudflare Worker is live and routing `hltmastery.com/nursing/resources/*` to MasteryPublishing
- links are rewritten
- static assets pass through
- public shell remains outside the structured content engine

## Immediate proxy and SEO issues
- JSON-LD `@id` missing `/nursing` prefix
- sitemap URLs missing `/nursing` prefix
- robots sitemap link wrong
- metadataBase wrong for proxied public route
- placeholder image fallbacks causing visible 404s

## Recommended fix sequence
1. set `NEXT_PUBLIC_SITE_URL=https://hltmastery.com/nursing`
2. fix JSON-LD URL generation to use the env-based site URL
3. replace placeholder image behavior
4. coordinate with Jason on worker rewrite behavior and `?_rsc=` paths
5. verify client-side navigation, sitemap, robots, and OG output

## Canonical content lane versus shell rule
- **MasteryPublishing** owns structured `/resources/**` content
- **Framer** owns shell and legacy or adjacent public surfaces
- **Cloudflare proxy** stitches the public experience
- **sidecar-system** remains upstream and may publish to more than one destination

## Content contract summary
Pulled from `CANONICAL_CONTENT_CONTRACT.md`:

### Required core identity fields
- `id`
- `katailyst_id`
- `slug`
- `title`
- `content_type`
- `category`
- `primary_product_id`

### Major field groups
- core content: `subtitle`, `excerpt`, `body_html`, `body_json`
- media: `hero_image_url`, `hero_image_alt`, `hero_video_url`, `og_image_url`
- relationships: product, author, topics
- structured blocks: `faq_json`, `stats_json`, `steps_json`, `comparison_json`, `citations`
- SEO: `meta_title`, `meta_description`, `canonical_url`, `noindex`
- publishing: `status`, `published_at`, `featured`, `sort_order`, `word_count`, `reading_time_minutes`

## CMS workflow summary
Pulled from `CMS_WORKFLOW.md`:
- Supabase Studio is the manual CMS surface
- products, topics, and authors are mostly reference data
- articles are added and edited in the `articles` table
- `article_topics` manages topic linkage
- `/api/revalidate` can be used for immediate refresh behavior

## Content engine requirements summary
Pulled from `CONTENT_ENGINE_REQUIREMENTS.md`:
- `/resources` is the all-resources hub
- `/resources/[product]` is the per-product hub
- `/resources/[product]/[slug]` is the individual article route
- `/resources/search` is the search page
- the engine supports seven products and a broad content-type matrix
- it is meant to feel visually aligned with product pages and HLT public experience

## Media lane doctrine
- Multimedia Mastery should be the preferred media generation lane
- Cloudinary should be the preferred storage and derivative system of record
- direct generation flows that bypass Cloudinary are structurally weaker
- hero image quality, persistence, tagging, and branding are real system requirements, not polish
- Multimedia Mastery should also follow the same Axon-aware repo-entry standard so media pipeline work is easier to inspect and clean up safely

## Current media gaps
- draft articles currently have missing hero images
- placeholder fallbacks are not reliable enough
- Multimedia Mastery integration into the article pipeline remains an important next step

## Cleanup and doc-polish standard for this lane
- sidecar-system, MasteryPublishing, and Multimedia4Mastery should all show Axon explicitly in their repo-entry doctrine
- cleanup work should use Axon for structure discovery, contract tracing, and impact review before larger changes
- publishing and media docs should stay operator-grade and call out live routes, payload contracts, ownership, and source-of-truth boundaries directly

## Framer coexistence strategy
- keep Framer for shell and legacy public lanes while the structured content lane proves itself
- do not rush migration for elegance alone
- compare speed, SEO, publishing velocity, and content quality before larger sunset decisions
