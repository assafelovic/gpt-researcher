# 01-ecosystem-atlas-master

> High-level map of the HLT ecosystem, with emphasis on system boundaries, ownership, and current doctrine.

## Core doctrine
- start with **Katailyst** for orientation and capability discovery
- use **Axon** second for repo and symbol comprehension across every active repo that is being cleaned up or maintained
- do not assume the current repo is the whole system
- verify live and runtime truth before making architectural claims
- prefer a few official large docs over sprawl
- make Axon visible in the operator docs and repo-entry doctrine, not buried as a specialist-only trick

## Main ecosystem components

### Katailyst
- capability canon
- MCP and registry surface
- orchestration center
- primary orientation layer for agents
- should increasingly absorb observability and warehouse-adjacent ideas into the existing Supabase-backed system instead of spawning fragmented parallel systems
- strategic posture: extend the already massively populated core system, because the goal is to become the armory rather than a set of disconnected side tools

### sidecar-system
- upstream article and destination orchestration surface
- article creation workflows
- publishing fan-out to downstream systems
- should carry the same Axon-first repo-entry doctrine as the other core repos

### MasteryPublishing
- canonical structured `/resources/**` lane
- Next.js content engine
- Supabase-backed content display and publish endpoint
- should expose Axon as a normal repo-comprehension and refactor-safety layer in its root docs

### Framer and HLTMastery shell
- public shell
- homepage, nav, footer, landing pages
- legacy and adjacent public content lanes like `/nursing/nclex-blog/*`

### Multimedia Mastery
- media generation and media workflow lane
- intended partner with Cloudinary for branded asset flow

### Cloudinary
- media system of record
- asset storage, derivatives, transformations, watermarking

### Agent Canvas
- coordination and plan surface
- should be part of the same Axon-backed cross-repo cleanup and documentation standard

### Evidence-Based Business
- measurement and feedback layer
- should increasingly function as the data warehouse and decision surface for the ecosystem, not just a side app
- should hold meaningful slices of app usage, conversion, financial, and content performance data that agents can consume directly
- should include Axon in the repo-entry pattern so analytics and schema work can be traversed safely

## Current architecture pattern: three-system article flow
1. sidecar-system creates and orchestrates article content
2. MasteryPublishing renders the canonical structured `/resources/**` lane
3. Framer owns the broader public shell and legacy public surfaces
4. Cloudflare proxy makes the structured lane appear under `hltmastery.com/nursing/resources/*`

## Public route ownership map
| Public route | Owner | Meaning |
|---|---|---|
| `/nursing/resources/*` | MasteryPublishing via proxy | canonical structured content lane |
| `/nursing/nclex-blog/*` | Framer | legacy or separate blog lane |
| `/nursing/fnp/resources/*` | Framer | Framer-managed resource lane |
| `/`, nav, footer, shell | Framer | main public shell |

## Important boundary rule
Do not confuse:
- public route ownership
- shell ownership
- canonical content ownership
- media ownership

These are separate questions.

## Repo-comprehension and cleanup standard
For the current cleanup pass, the major active repos should all be documented as Axon-aware surfaces.

Minimum expectation:
- agents start with Katailyst for ecosystem orientation
- then use Axon for repo structure, symbol context, impact analysis, and dead-code review
- then read the surrounding files before edits
- then update the canonical docs so Axon posture stays explicit and current

## Public verification status
Publicly verified today:
- `hltmastery.com/nursing/resources` is live as the structured public lane
- `hltmastery.com/nursing/nclex-blog` is still a separate live public lane
- Multimedia Mastery currently redirects to login
- Katailyst is live but protected behind auth for deeper surfaces
