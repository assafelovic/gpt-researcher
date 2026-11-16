---
sidebar_label: Image Understanding
sidebar_position: 6
---

# 🖼️ Image Understanding (Vision)

GPT Researcher scrapes the images of the pages it reads, but until now only the
**text** of a page reached the report writer - figures, charts and diagrams
embedded as images were silently dropped. With the optional vision analyzer, the
most relevant scraped images are sent to a vision-language model (VLM) and a
compact caption/OCR block is injected into the research context, so reports can
reason about visual evidence too.

## How it works

1. The scraper already collects image URLs for every source page.
2. The `VisionAnalyzer` skill ranks and de-duplicates those images, then keeps
   a few per sub-query (`VISION_MAX_IMAGES`, `VISION_MAX_IMAGES_PER_SOURCE`).
3. Each image is downloaded (with the same SSRF guard as page scraping), size
   capped, and sent to an OpenAI-compatible VLM endpoint.
4. The VLM returns a caption, any legible text (OCR) and a relevance verdict,
   which the analyzer attaches to the source as `image_captions` and appends
   to the source content as a "Visual evidence" block.
5. That content flows through the normal context compression pipeline, so the
   report writer and the vector store can use it without further changes.

Everything is opt-in and fails open: a slow endpoint, a blocked image or a
malformed answer is logged and skipped, and the standard research flow keeps
working.

## Quick start

### 1. Choose a VLM endpoint

Any OpenAI-compatible chat-completions endpoint works. Examples:

```bash
# DashScope / Qwen-VL
export VISION_ENABLED=true
export VISION_MODEL=qwen2.5-vl-3b-instruct
export VISION_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export VISION_API_KEY=sk-...

# OpenAI
export VISION_ENABLED=true
export VISION_MODEL=gpt-4o-mini
export VISION_BASE_URL=https://api.openai.com/v1
export VISION_API_KEY=sk-...

# Local vLLM / Ollama shim
export VISION_ENABLED=true
export VISION_MODEL=Qwen/Qwen2.5-VL-3B-Instruct
export VISION_BASE_URL=http://127.0.0.1:8000/v1
export VISION_API_KEY=EMPTY
```

### 2. Run research as usual

```python
import asyncio
from gpt_researcher import GPTResearcher

async def main():
    researcher = GPTResearcher(
        query="How does fenofibrate affect mortality in heart failure trials?",
        report_type="research_report",
    )
    report = await researcher.conduct_research()
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
```

When `VISION_ENABLED=true` the research context (and therefore the report)
contains a short visual-evidence block for the pages that carried usable
images.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `VISION_ENABLED` | `false` | Master switch for image understanding. |
| `VISION_MODEL` | `gpt-4o-mini` | VLM model name passed to the endpoint. |
| `VISION_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL (no trailing `/chat/completions`). |
| `VISION_API_KEY` | - | API key; falls back to `VISION_API_KEY` then `OPENAI_API_KEY`. |
| `VISION_MAX_IMAGES` | `3` | Images analyzed per sub-query (global cap). |
| `VISION_MAX_IMAGES_PER_SOURCE` | `2` | Images analyzed per scraped page. |
| `VISION_MAX_IMAGE_BYTES` | `8000000` | Skip images larger than this. |
| `VISION_TIMEOUT` | `60.0` | Per-request timeout in seconds. |
| `VISION_EMBED_IN_CONTEXT` | `true` | Append captions to the source content; the `image_captions` field is always stored. |

## What gets injected

Each enriched source gains an `image_captions` list and, when
`VISION_EMBED_IN_CONTEXT=true`, a block like:

```text
[Visual evidence from images in this source]
- Bar chart of 12-month mortality by treatment arm. Visible text: Placebo 12% / Treatment 8%
```

## Notes and limits

- Every analyzed image costs one VLM call, so keep the caps small (the
  defaults target 2-3 calls per sub-query).
- Images that are blocked by hotlink protection or served behind cookies are
  skipped; the page text is still used.
- OCR quality depends on the VLM; small axis labels may be missed.
- The analyzer shares the SSRF guard used for page scraping, so it will not
  fetch private or internal addresses unless `ALLOW_PRIVATE_URLS=true`.
