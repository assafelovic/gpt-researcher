# RFC: High-Quality Content & Image Scraping Architecture

> **Status**: Proposal
> **Author**: Community Contributor
> **Created**: 2026-01-31
> **Target Version**: v4.x

## Summary

This proposal analyzes the current scraping capabilities in GPT-Researcher and recommends an optimal architecture for obtaining high-quality text content and relevant images from web sources.

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [Built-in vs External Tools Comparison](#2-built-in-vs-external-tools-comparison)
3. [Recommended Hybrid Architecture](#3-recommended-hybrid-architecture)
4. [Implementation Guide](#4-implementation-guide)
5. [Decision Matrix: When to Use What](#5-decision-matrix-when-to-use-what)
6. [Cost Analysis](#6-cost-analysis)

---

## 1. Current Architecture Analysis

### 1.1 Current Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Current GPT-Researcher Flow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   User Query                                                            │
│       │                                                                 │
│       ▼                                                                 │
│   Tavily Search (Basic Mode)                                            │
│   - Returns: URL + short summary                                        │
│   - Cost: 1 credit per query                                            │
│   - Does NOT return: raw_content, images                                │
│       │                                                                 │
│       ▼                                                                 │
│   URL List Extraction                                                   │
│   - Only href is used                                                   │
│   - Summary content (body) is DISCARDED ❌                              │
│       │                                                                 │
│       ▼                                                                 │
│   BeautifulSoup Scraping (Default)                                      │
│   - Re-fetches each URL                                                 │
│   - Extracts text + images from HTML                                    │
│   - May fail on JS-rendered pages                                       │
│       │                                                                 │
│       ▼                                                                 │
│   Context Compression                                                   │
│   - Vector similarity filtering                                         │
│   - Returns relevant chunks                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Current Configuration

```python
# Default settings in gpt_researcher/config/variables/default.py
{
    "SCRAPER": "bs",                    # BeautifulSoup (basic HTML parser)
    "MAX_SCRAPER_WORKERS": 15,          # Parallel scraping workers
    "SCRAPER_RATE_LIMIT_DELAY": 0.0,    # No rate limiting
}

# Tavily search settings in retrievers/tavily/tavily_search.py
results = self._search(
    self.query,
    search_depth="basic",           # Basic mode only
    include_raw_content=False,      # No full content
    include_images=False,           # No images
)
```

### 1.3 Problems with Current Approach

| Issue | Impact | Severity |
|-------|--------|----------|
| Tavily summary discarded | Wasted API response data | Medium |
| No raw_content from Tavily | Must re-scrape every URL | High |
| No images from Tavily | Missing search-related images | Medium |
| BS fails on JS pages | Missing content from React/Vue sites | High |
| No anti-bot handling | Blocked by many sites | Medium |

---

## 2. Built-in vs External Tools Comparison

### 2.1 Available Scraping Tools

#### Built-in Tools (Free)

| Tool | File Location | Capabilities | Limitations |
|------|---------------|--------------|-------------|
| **BeautifulSoup** | `scraper/beautiful_soup/` | Basic HTML parsing, fast | No JS rendering, blocked by anti-bot |
| **WebBaseLoader** | `scraper/web_base_loader/` | LangChain integration | Same as BS |
| **Browser (Selenium)** | `scraper/browser/` | JS rendering, screenshots | Slow, resource heavy |
| **NoDriver** | `scraper/browser/nodriver_scraper.py` | Headless browser, stealth | Complex setup |
| **PyMuPDF** | `scraper/pymupdf/` | PDF extraction | PDF only |
| **ArXiv** | `scraper/arxiv/` | Academic papers | ArXiv only |

#### External API Tools (Paid)

| Tool | File Location | Capabilities | Cost |
|------|---------------|--------------|------|
| **Tavily Extract** | `scraper/tavily_extract/` | Professional extraction, clean content | 1 credit / 5 URLs |
| **FireCrawl** | `scraper/firecrawl/` | LLM-optimized, handles JS | ~$0.001 / page |
| **Tavily Search Advanced** | `retrievers/tavily/` | Raw content + images in search | 2 credits / query |

### 2.2 Detailed Capability Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          Scraper Capability Matrix                                   │
├──────────────────┬───────┬───────┬─────────┬─────────┬──────────┬──────────────────┤
│ Capability       │  BS   │Browser│NoDriver │ Tavily  │ FireCrawl│ Tavily Search Adv│
│                  │       │       │         │ Extract │          │                  │
├──────────────────┼───────┼───────┼─────────┼─────────┼──────────┼──────────────────┤
│ Static HTML      │  ✅   │  ✅   │   ✅    │   ✅    │    ✅    │       ✅         │
│ JS Rendering     │  ❌   │  ✅   │   ✅    │   ✅    │    ✅    │       ✅         │
│ Anti-bot Bypass  │  ❌   │  ⚠️   │   ✅    │   ✅    │    ✅    │       ✅         │
│ Clean Content    │  ⚠️   │  ⚠️   │   ⚠️    │   ✅    │    ✅    │       ✅         │
│ Image Extraction │  ✅   │  ✅   │   ✅    │   ⚠️    │    ✅    │       ✅         │
│ Speed            │  ⚡⚡⚡ │  ⚡   │   ⚡⚡   │   ⚡⚡   │    ⚡⚡   │       ⚡⚡⚡       │
│ Cost             │ Free  │ Free  │  Free   │  Paid   │   Paid   │      Paid        │
│ Reliability      │  ⚠️   │  ⚠️   │   ✅    │   ✅    │    ✅    │       ✅         │
│ Setup Complexity │  Low  │ High  │  Medium │   Low   │   Low    │       Low        │
└──────────────────┴───────┴───────┴─────────┴─────────┴──────────┴──────────────────┘

Legend: ✅ = Full support, ⚠️ = Partial/Limited, ❌ = Not supported
```

### 2.3 Content Quality Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Content Quality by Tool                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   BeautifulSoup Output:                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │ "Home About Contact Login                                        │  │
│   │  Article Title                                                   │  │
│   │  By Author | Date                                                │  │
│   │  Share Tweet                                                     │  │
│   │  The actual content starts here but mixed with navigation...    │  │
│   │  Subscribe Newsletter Footer Links Copyright..."                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│   Quality: ⭐⭐ (includes noise)                                        │
│                                                                         │
│   Tavily Extract / FireCrawl Output:                                   │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │ "Article Title                                                   │  │
│   │                                                                  │  │
│   │  The actual content starts here. This is clean, well-formatted │  │
│   │  text that has been intelligently extracted from the page,      │  │
│   │  removing all navigation, ads, and irrelevant elements..."      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│   Quality: ⭐⭐⭐⭐⭐ (clean, LLM-ready)                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Image Source Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Two Types of Images                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Type 1: Search-Related Images (Tavily include_images)                 │
│   ═══════════════════════════════════════════════════                   │
│   Source: Search engine image results                                   │
│   Content: General images related to query                              │
│   Example: Search "Tesla" → Tesla car photos, logo, Elon Musk          │
│   Quality: Good for general illustration                                │
│   Limitation: May not match specific article content                    │
│                                                                         │
│   Type 2: Page-Embedded Images (HTML <img> scraping)                    │
│   ════════════════════════════════════════════════════                  │
│   Source: Extracted from webpage HTML                                   │
│   Content: Article diagrams, charts, infographics                       │
│   Example: Sales chart in an analysis article                           │
│   Quality: Directly relevant to article content                         │
│   Limitation: Requires page scraping, may miss lazy-loaded images       │
│                                                                         │
│   🎯 Recommendation: Capture BOTH types for comprehensive results       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Recommended Hybrid Architecture

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Recommended: Hybrid Scraping Architecture                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                         User Query                                      │
│                            │                                            │
│                            ▼                                            │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  Stage 1: Tavily Search Advanced                                │   │
│   │  ══════════════════════════════                                 │   │
│   │  Parameters:                                                    │   │
│   │    search_depth: "advanced"                                     │   │
│   │    include_raw_content: true                                    │   │
│   │    include_images: true                                         │   │
│   │    include_image_descriptions: true                             │   │
│   │                                                                 │   │
│   │  Returns:                                                       │   │
│   │    ├─ results[].url           (URLs)                           │   │
│   │    ├─ results[].content       (Summary)                        │   │
│   │    ├─ results[].raw_content   (Full page content) ✅           │   │
│   │    └─ images[]                (Search-related images) ✅       │   │
│   └──────────────────────────────┬─────────────────────────────────┘   │
│                                  │                                      │
│                    ┌─────────────┴─────────────┐                       │
│                    │                           │                       │
│                    ▼                           ▼                       │
│   ┌──────────────────────────┐   ┌──────────────────────────┐         │
│   │  raw_content EXISTS      │   │  raw_content EMPTY/SHORT │         │
│   │  & length > 500 chars    │   │  or JS-rendered page     │         │
│   └────────────┬─────────────┘   └────────────┬─────────────┘         │
│                │                              │                        │
│                ▼                              ▼                        │
│   ┌──────────────────────────┐   ┌──────────────────────────┐         │
│   │  Use Tavily Content      │   │  Stage 2: Fallback Scrape│         │
│   │  directly (no re-scrape) │   │  ════════════════════════│         │
│   │                          │   │  Browser/NoDriver/       │         │
│   │  Cost: 0 extra           │   │  FireCrawl for JS pages  │         │
│   └────────────┬─────────────┘   └────────────┬─────────────┘         │
│                │                              │                        │
│                │                              ├─→ Page Content         │
│                │                              └─→ Page Images (<img>)  │
│                │                                       │               │
│                └──────────────┬────────────────────────┘               │
│                               │                                        │
│                               ▼                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  Stage 3: Content & Image Aggregation                          │   │
│   │  ═════════════════════════════════════                          │   │
│   │                                                                 │   │
│   │  Text Content:                                                  │   │
│   │    - Primary: Tavily raw_content                               │   │
│   │    - Fallback: Browser-scraped content                         │   │
│   │                                                                 │   │
│   │  Images (merged & deduplicated):                               │   │
│   │    - Tavily search images (general relevance)                  │   │
│   │    - Page-embedded images (article-specific)                   │   │
│   │                                                                 │   │
│   │  Image Ranking:                                                │   │
│   │    1. Page images with class: featured/hero/main (score: 4)   │   │
│   │    2. Large page images > 800x500 (score: 3)                  │   │
│   │    3. Tavily search images (score: 2)                         │   │
│   │    4. Medium page images > 500x300 (score: 1)                 │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Quality Tiers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Three Quality Tiers                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Tier 1: Budget Mode (Current Default)                                 │
│   ═══════════════════════════════════                                   │
│   Search: Tavily Basic (1 credit)                                       │
│   Scrape: BeautifulSoup (free)                                          │
│   Images: Page <img> only                                               │
│   Cost: ~1 credit/query                                                 │
│   Quality: ⭐⭐⭐                                                        │
│   Use when: Budget limited, simple static websites                      │
│                                                                         │
│   Tier 2: Balanced Mode (Recommended)                                   │
│   ════════════════════════════════════                                  │
│   Search: Tavily Advanced (2 credits)                                   │
│   Scrape: Selective (only when raw_content missing)                     │
│   Images: Tavily images + Page <img>                                    │
│   Cost: ~2-3 credits/query                                              │
│   Quality: ⭐⭐⭐⭐                                                       │
│   Use when: General research, mixed website types                       │
│                                                                         │
│   Tier 3: Maximum Quality Mode                                          │
│   ═══════════════════════════════                                       │
│   Search: Tavily Advanced (2 credits)                                   │
│   Scrape: Tavily Extract or FireCrawl for all URLs                     │
│   Images: All sources + image descriptions                              │
│   Cost: ~5-10 credits/query                                             │
│   Quality: ⭐⭐⭐⭐⭐                                                      │
│   Use when: Critical research, complex JS-heavy sites                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation Guide

### 4.1 Configuration Changes

#### Option A: Environment Variables

```bash
# .env file

# ═══════════════════════════════════════════════════════════════
# Tier 1: Budget Mode (Current Default)
# ═══════════════════════════════════════════════════════════════
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=basic
SCRAPER=bs

# ═══════════════════════════════════════════════════════════════
# Tier 2: Balanced Mode (Recommended)
# ═══════════════════════════════════════════════════════════════
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=browser  # Fallback for JS pages

# ═══════════════════════════════════════════════════════════════
# Tier 3: Maximum Quality Mode
# ═══════════════════════════════════════════════════════════════
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=tavily_extract  # or firecrawl
FIRECRAWL_API_KEY=your_key  # if using firecrawl
```

#### Option B: Code Modification

```python
# gpt_researcher/retrievers/tavily/tavily_search.py

# BEFORE (current)
results = self._search(
    self.query,
    search_depth="basic",
    include_raw_content=False,
    include_images=False,
)

# AFTER (recommended)
results = self._search(
    self.query,
    search_depth=os.getenv("TAVILY_SEARCH_DEPTH", "advanced"),
    include_raw_content=os.getenv("TAVILY_INCLUDE_RAW_CONTENT", "true").lower() == "true",
    include_images=os.getenv("TAVILY_INCLUDE_IMAGES", "true").lower() == "true",
    include_image_descriptions=True,
)

# Also modify the return to include raw_content
search_response = [
    {
        "href": obj["url"],
        "body": obj.get("raw_content") or obj["content"],  # Prefer raw_content
        "title": obj.get("title", ""),
        "images": obj.get("images", []),
    }
    for obj in sources
]
```

### 4.2 New Hybrid Scraper Implementation

```python
# gpt_researcher/skills/hybrid_content_fetcher.py

"""
Hybrid Content Fetcher for high-quality text and images.
Combines Tavily Advanced search with selective fallback scraping.
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContentResult:
    """Structured content result."""
    url: str
    content: str
    title: str
    images: List[Dict[str, Any]]
    source: str  # 'tavily_raw', 'browser_scrape', 'tavily_extract'
    quality_score: float


@dataclass
class ImageResult:
    """Structured image result."""
    url: str
    description: str
    source: str  # 'tavily_search', 'page_embedded'
    score: float


class HybridContentFetcher:
    """
    Fetches high-quality content and images using a hybrid approach:
    1. Tavily Advanced for raw_content + search images
    2. Selective browser scraping for JS pages or missing content
    3. Intelligent image aggregation from multiple sources
    """

    def __init__(self, researcher):
        self.researcher = researcher
        self.cfg = researcher.cfg
        self.min_content_length = 500
        self.max_images = 15

        # Image collections
        self.tavily_images: List[ImageResult] = []
        self.page_images: List[ImageResult] = []

    async def fetch(
        self,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Main entry point for hybrid content fetching.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            Dict containing contents and images
        """
        # Stage 1: Tavily Advanced Search
        search_results = await self._tavily_advanced_search(query, max_results)

        # Collect Tavily search images
        self._collect_tavily_images(search_results.get('images', []))

        # Stage 2: Process each result
        contents = await self._process_search_results(search_results['results'])

        # Stage 3: Aggregate and deduplicate images
        all_images = self._aggregate_images()

        return {
            'contents': contents,
            'images': all_images,
            'metadata': {
                'total_contents': len(contents),
                'tavily_images_count': len(self.tavily_images),
                'page_images_count': len(self.page_images),
                'final_images_count': len(all_images),
            }
        }

    async def _tavily_advanced_search(
        self,
        query: str,
        max_results: int
    ) -> Dict[str, Any]:
        """Execute Tavily Advanced search."""
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

            return client.search(
                query=query,
                search_depth="advanced",
                include_raw_content=True,
                include_images=True,
                include_image_descriptions=True,
                max_results=max_results,
            )
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {'results': [], 'images': []}

    async def _process_search_results(
        self,
        results: List[Dict]
    ) -> List[ContentResult]:
        """Process search results, using fallback scraping when needed."""
        contents = []

        for result in results:
            url = result.get('url', '')
            raw_content = result.get('raw_content', '')

            # Check if raw_content is sufficient
            if raw_content and len(raw_content) >= self.min_content_length:
                # Use Tavily raw_content directly
                contents.append(ContentResult(
                    url=url,
                    content=raw_content,
                    title=result.get('title', ''),
                    images=[],
                    source='tavily_raw',
                    quality_score=0.9
                ))
                logger.info(f"Using Tavily raw_content for {url}")
            else:
                # Fallback: scrape the page
                scraped = await self._fallback_scrape(url)
                if scraped:
                    contents.append(scraped)
                    # Collect page images
                    for img in scraped.images:
                        self.page_images.append(ImageResult(
                            url=img.get('url', ''),
                            description=img.get('alt', ''),
                            source='page_embedded',
                            score=img.get('score', 1)
                        ))

        return contents

    async def _fallback_scrape(self, url: str) -> Optional[ContentResult]:
        """Fallback scraping for pages without raw_content."""
        try:
            scraper_type = self.cfg.scraper

            if scraper_type == 'browser':
                from gpt_researcher.scraper import BrowserScraper
                scraper = BrowserScraper(url)
            elif scraper_type == 'nodriver':
                from gpt_researcher.scraper import NoDriverScraper
                scraper = NoDriverScraper(url)
            elif scraper_type == 'tavily_extract':
                from gpt_researcher.scraper import TavilyExtract
                scraper = TavilyExtract(url)
            else:
                from gpt_researcher.scraper import BeautifulSoupScraper
                scraper = BeautifulSoupScraper(url)

            if hasattr(scraper, 'scrape_async'):
                content, images, title = await scraper.scrape_async()
            else:
                content, images, title = await asyncio.get_running_loop().run_in_executor(
                    None, scraper.scrape
                )

            if content and len(content) >= 100:
                logger.info(f"Fallback scrape successful for {url}")
                return ContentResult(
                    url=url,
                    content=content,
                    title=title,
                    images=images,
                    source=f'{scraper_type}_scrape',
                    quality_score=0.7
                )
        except Exception as e:
            logger.error(f"Fallback scrape failed for {url}: {e}")

        return None

    def _collect_tavily_images(self, images: List) -> None:
        """Collect images from Tavily search results."""
        for img in images:
            if isinstance(img, str):
                self.tavily_images.append(ImageResult(
                    url=img,
                    description='',
                    source='tavily_search',
                    score=2.0
                ))
            elif isinstance(img, dict):
                self.tavily_images.append(ImageResult(
                    url=img.get('url', ''),
                    description=img.get('description', ''),
                    source='tavily_search',
                    score=2.0
                ))

    def _aggregate_images(self) -> List[Dict[str, Any]]:
        """Aggregate and deduplicate images from all sources."""
        seen_urls: Set[str] = set()
        aggregated: List[Dict[str, Any]] = []

        # Combine all images, prioritizing page images
        all_images = self.page_images + self.tavily_images

        # Sort by score (higher first)
        all_images.sort(key=lambda x: x.score, reverse=True)

        for img in all_images:
            if img.url and img.url not in seen_urls:
                seen_urls.add(img.url)
                aggregated.append({
                    'url': img.url,
                    'description': img.description,
                    'source': img.source,
                    'score': img.score,
                })

                if len(aggregated) >= self.max_images:
                    break

        return aggregated
```

---

## 5. Decision Matrix: When to Use What

### 5.1 Scraper Selection Guide

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Scraper Decision Tree                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Is the target site JS-heavy (React/Vue/Angular)?                      │
│       │                                                                 │
│       ├─ YES ──→ Is budget available for API?                          │
│       │              │                                                  │
│       │              ├─ YES ──→ Use Tavily Extract or FireCrawl        │
│       │              │          (Best quality, reliable)                │
│       │              │                                                  │
│       │              └─ NO ───→ Use Browser or NoDriver                │
│       │                         (Free, but slower)                      │
│       │                                                                 │
│       └─ NO ───→ Does site have anti-bot protection?                   │
│                      │                                                  │
│                      ├─ YES ──→ Use NoDriver or Tavily Extract         │
│                      │          (Stealth capabilities)                  │
│                      │                                                  │
│                      └─ NO ───→ Is content quality critical?           │
│                                     │                                   │
│                                     ├─ YES ──→ Use Tavily Advanced     │
│                                     │          (raw_content included)   │
│                                     │                                   │
│                                     └─ NO ───→ Use BeautifulSoup       │
│                                                (Free, fast, sufficient) │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Use Case Recommendations

| Use Case | Recommended Setup | Cost | Notes |
|----------|------------------|------|-------|
| **Quick research, simple sites** | Tavily Basic + BS | $ | Default, works for most blogs |
| **General research** | Tavily Advanced + Browser fallback | $$ | Best balance |
| **Academic research** | Tavily Advanced + ArXiv scraper | $$ | Papers handled specially |
| **News aggregation** | Tavily Advanced (topic=news) | $$ | Optimized for news |
| **E-commerce research** | Tavily Advanced + NoDriver | $$$ | Handles JS shops |
| **Technical documentation** | Tavily Extract | $$$ | Clean extraction |
| **Social media content** | Browser + custom auth | $$ | May need login |
| **Maximum quality** | Tavily Advanced + FireCrawl | $$$$ | Best possible quality |

### 5.3 Image Source Selection

| Scenario | Image Sources | Configuration |
|----------|---------------|---------------|
| **General illustration** | Tavily search images | `include_images=true` |
| **Article diagrams/charts** | Page `<img>` scraping | `SCRAPER=browser` |
| **Both** | Hybrid (recommended) | Advanced + Browser |
| **No images needed** | Disable | `include_images=false` |

---

## 6. Cost Analysis

### 6.1 Tavily Credit Costs

| Operation | Credits | Notes |
|-----------|---------|-------|
| Search Basic | 1 | Summary only |
| Search Advanced | 2 | Includes raw_content |
| Extract | 1 per 5 URLs | Dedicated extraction |
| Include Images | +0 | Free with search |

### 6.2 Cost Comparison by Tier

Assuming 5 sub-queries per research, 10 URLs per query:

| Tier | Search | Scrape | Total/Research | Monthly (100 researches) |
|------|--------|--------|----------------|--------------------------|
| **Budget** | 5×1 = 5 | Free (BS) | ~5 credits | 500 credits |
| **Balanced** | 5×2 = 10 | Selective | ~12 credits | 1,200 credits |
| **Maximum** | 5×2 = 10 | 50/5 = 10 | ~20 credits | 2,000 credits |

### 6.3 Quality vs Cost Trade-off

```
Quality ▲
        │
    ⭐⭐⭐⭐⭐ │                              ● Maximum (FireCrawl)
        │                         ●
    ⭐⭐⭐⭐ │               ● Balanced (Recommended)
        │          ●
    ⭐⭐⭐ │    ● Budget (Current Default)
        │
    ⭐⭐ │
        │
        └────────────────────────────────────────► Cost
              $      $$      $$$      $$$$
```

---

## 7. Summary & Recommendations

### For Most Users (Balanced Mode)

```bash
# .env
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=browser
```

**Benefits:**
- High-quality text from Tavily raw_content
- Search-related images from Tavily
- Page-embedded images from browser scraping
- JS page handling via browser fallback
- Reasonable cost (~2 credits/query)

### For Budget-Conscious Users

Keep current defaults, but consider:
- Upgrading to `SCRAPER=nodriver` for better JS handling (still free)
- Using `SCRAPER=browser` for important research tasks

### For Maximum Quality

```bash
# .env
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=firecrawl
FIRECRAWL_API_KEY=your_key
```

---

## References

- [Tavily Search API Documentation](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- [Tavily Extract API Documentation](https://docs.tavily.com/documentation/api-reference/endpoint/extract)
- [FireCrawl Documentation](https://docs.firecrawl.dev/)
- [Tavily Search vs Extract APIs](https://medium.com/@sofia_51582/tavilys-search-vs-extract-apis-and-when-to-use-each-67cc70edd610)
- [Basic vs Advanced Search](https://help.tavily.com/articles/6938147944-basic-vs-advanced-search-what-s-the-difference)
