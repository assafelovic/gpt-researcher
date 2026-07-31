#!/usr/bin/env python3
"""Build my-docs/recruiting/content-inventory.md from www.nursingmastery.com.

Uses the Firecrawl API (same plan the researcher scrapes with):
  1. /v1/map    — discover every URL on the site.
  2. /v1/scrape — pull title + description metadata for the top pages.

Run locally (`FIRECRAWL_API_KEY=... python scripts/build_recruiting_inventory.py`)
or let the weekly audience-sweep GitHub Action refresh it.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

FIRECRAWL_BASE = os.getenv("FIRECRAWL_SERVER_URL", "https://api.firecrawl.dev").rstrip("/")
SITE = os.getenv("RECRUITING_SITE_URL", "https://www.nursingmastery.com")
OUTPUT = Path(os.getenv("RECRUITING_INVENTORY_PATH", "my-docs/recruiting/content-inventory.md"))
# Metadata scrapes cost credits; cap how many pages get enriched per run.
SCRAPE_LIMIT = int(os.getenv("RECRUITING_SCRAPE_LIMIT", "40"))


def _firecrawl(path: str, body: dict) -> dict:
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        sys.exit("FIRECRAWL_API_KEY is required")
    request = urllib.request.Request(
        f"{FIRECRAWL_BASE}{path}",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def map_site() -> list[str]:
    body = _firecrawl("/v1/map", {"url": SITE, "limit": 500})
    links = body.get("links") or []
    urls = []
    for link in links:
        url = link if isinstance(link, str) else link.get("url", "")
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc.endswith("nursingmastery.com"):
            continue
        # Skip assets and query-duplicated URLs.
        if parsed.path.rsplit(".", 1)[-1] in {"png", "jpg", "svg", "css", "js", "ico", "xml"}:
            continue
        clean = f"https://{parsed.netloc}{parsed.path}".rstrip("/") or SITE
        if clean not in urls:
            urls.append(clean)
    return urls


def scrape_metadata(url: str) -> dict:
    try:
        body = _firecrawl(
            "/v1/scrape",
            {"url": url, "formats": ["markdown"], "onlyMainContent": True},
        )
    except Exception as error:  # noqa: BLE001 - per-page failures shouldn't kill the run
        return {"url": url, "error": type(error).__name__}
    data = body.get("data") or {}
    metadata = data.get("metadata") or {}
    markdown = data.get("markdown") or ""
    first_heading = next(
        (line.lstrip("# ").strip() for line in markdown.splitlines() if line.startswith("#")),
        "",
    )
    return {
        "url": url,
        "title": metadata.get("title") or first_heading or url,
        "description": (metadata.get("description") or "").strip(),
        "words": len(markdown.split()),
    }


def section_of(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/")
    return path.split("/")[0] or "home"


def main() -> None:
    urls = map_site()
    print(f"mapped {len(urls)} urls on {SITE}")

    by_section: dict[str, list[str]] = defaultdict(list)
    for url in urls:
        by_section[section_of(url)].append(url)

    # Enrich the most load-bearing pages: home + shallow paths first.
    prioritized = sorted(urls, key=lambda u: urllib.parse.urlparse(u).path.count("/"))
    enriched: dict[str, dict] = {}
    for url in prioritized[:SCRAPE_LIMIT]:
        enriched[url] = scrape_metadata(url)
        print(f"scraped {url}")
        time.sleep(0.5)

    lines = [
        "# Nursing Mastery content inventory (generated)",
        "",
        f"Source: {SITE} — {len(urls)} pages mapped via Firecrawl on "
        f"{time.strftime('%Y-%m-%d')}. Rebuild with "
        "`python scripts/build_recruiting_inventory.py`.",
        "",
    ]
    for section in sorted(by_section, key=lambda s: (-len(by_section[s]), s)):
        section_urls = by_section[section]
        lines.append(f"## {section} ({len(section_urls)} pages)")
        lines.append("")
        for url in sorted(section_urls):
            meta = enriched.get(url)
            if meta and not meta.get("error"):
                title = str(meta.get("title", url)).replace("|", "-")
                description = str(meta.get("description", "")).replace("|", "-")
                extra = f" — {description}" if description else ""
                lines.append(f"- [{title}]({url}){extra}")
            else:
                lines.append(f"- {url}")
        lines.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(urls)} pages, {len(enriched)} enriched)")


if __name__ == "__main__":
    main()
