# RFC: Firefox-based stealth scraper backend

> Status: Proposal
> Author: Community contributor
> Created: 2026-05-26
> Target version: TBD
> Tracking discussion: TBD

## Overview

Proposal to add an optional `invisible_firefox` scraper backend under `gpt_researcher/scraper/`, parallel to the existing `firecrawl`, `browser`, `web_base_loader`, and `tavily_extract` backends.

## Motivation

A growing share of research-relevant pages sit behind Cloudflare, Akamai, Datadome, or hCaptcha. The default backends and Firecrawl path return empty content or 403 on those domains. Relevant open issues:

- #1685 (anybrowse MCP for Cloudflare)
- #1081 (Crunchbase Cloudflare block)
- #1602 (Firecrawl returns empty results)
- #1404 (self-hosted Firecrawl returns 0)

## Proposed backend

A new `gpt_researcher/scraper/invisible_firefox/` module wrapping `invisible_playwright` (https://github.com/feder-cr/invisible_playwright), which itself drives a patched Firefox 150 binary (https://github.com/feder-cr/invisible_firefox, MPL-2, same license as Firefox upstream). Fingerprint patches applied at the C++ source level so there are no JS shims to detect.

Selected when the user sets `SCRAPER=invisible_firefox` in `.env`. Optional dependency, only imported when selected.

## Out of scope

No changes to existing backends. No change to default `SCRAPER`. Backend selection remains user-driven via environment.

## Maintenance

Issues against the backend route to feder-cr/invisible_playwright. Only ask of this repo would be the new scraper module file plus a small registration entry in `gpt_researcher/scraper/scraper.py`.
