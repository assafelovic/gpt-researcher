# GPT Researcher — Image Auto-Generation Pipeline

> This document maps out how GPT Researcher automatically generates and embeds AI images into research reports. It covers configuration, prompt engineering, provider APIs, file-system output, and the end-to-end flow from a research query to a finished report with illustrations.

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration & Environment Variables](#configuration--environment-variables)
3. [Architecture at a Glance](#architecture-at-a-glance)
4. [Step-by-Step Pipeline](#step-by-step-pipeline)
5. [Prompt Generation Deep Dive](#prompt-generation-deep-dive)
6. [Image Providers](#image-providers)
7. [File System Layout](#file-system-layout)
8. [Report Embedding](#report-embedding)
9. [Key Code References](#key-code-references)

---

## Overview

GPT Researcher can automatically generate contextually relevant diagrams, infographics, and conceptual illustrations for research reports. The feature is **opt-in** (disabled by default) and supports two image-generation backends:

- **Google** (Gemini/Imagen) — recommended; free tier available via `gemini-2.5-flash-image`
- **ModelsLab** (Flux, SDXL, Stable Diffusion, and 50k+ community models)

Images are generated in one of three ways:

1. **Pre-generation** — Images are planned and generated *after* web research finishes but *before* the report is written. This yields the best UX because the LLM writer knows the images exist and can weave them into the narrative.
2. **Post-report generation** — A completed report is analyzed section-by-section; images are generated for the sections that would benefit most from visualization and then embedded inline.
3. **Placeholder replacement** — The report writer inserts `[IMAGE: description]` tags; a post-processor finds these tags, generates images, and replaces them with markdown image syntax.

---

## Configuration & Environment Variables

All image-generation settings can be controlled via environment variables (`.env` file) or a JSON config file. Environment variables always take precedence.

| Variable | Type | Default | Description |
|---|---|---|---|
| `IMAGE_GENERATION_ENABLED` | bool | `false` | Master on/off switch. Must be `true` for any image generation to run. |
| `IMAGE_GENERATION_PROVIDER` | string | `google` | Backend to use. Options: `google` or `modelslab`. |
| `IMAGE_GENERATION_MODEL` | string | `models/gemini-2.5-flash-image` | Model identifier. See provider sections below for valid values. |
| `IMAGE_GENERATION_MAX_IMAGES` | int | `3` | Hard cap on the number of images generated per research report. |
| `IMAGE_GENERATION_STYLE` | string | `dark` | Visual theme appended to every prompt. Options: `dark`, `light`, `auto`. |
| `GOOGLE_API_KEY` | string | — | Required when provider is `google`. Also accepts `GEMINI_API_KEY`. |
| `MODELSLAB_API_KEY` | string | — | Required when provider is `modelslab`. Get one at modelslab.com/account/api-key. |

### Minimal `.env` Example (Google — Free Tier)

```bash
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
GOOGLE_API_KEY=AIza...

# Enable image generation
IMAGE_GENERATION_ENABLED=true
IMAGE_GENERATION_PROVIDER=google
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image
IMAGE_GENERATION_MAX_IMAGES=3
IMAGE_GENERATION_STYLE=dark
```

### Minimal `.env` Example (ModelsLab)

```bash
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
MODELSLAB_API_KEY=...

IMAGE_GENERATION_ENABLED=true
IMAGE_GENERATION_PROVIDER=modelslab
IMAGE_GENERATION_MODEL=flux
IMAGE_GENERATION_MAX_IMAGES=3
```

### Where Defaults Live

- **Default values** → `gpt_researcher/config/variables/default.py`
- **Type definitions** → `gpt_researcher/config/variables/base.py`
- **Env-var loading & precedence** → `gpt_researcher/config/config.py` (`_set_attributes()`)

The `Config` class reads the `BaseConfig` TypedDict, iterates over every key, and checks `os.getenv(key)`. If an env var exists, it is cast to the correct Python type (bool, int, float, list, dict, or str) and stored as a lowercase attribute on the config instance (e.g., `cfg.image_generation_enabled`).

---

## Architecture at a Glance

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Query    │────▶│  GPTResearcher   │────▶│  Web Research   │
│  (with images   │     │   (agent.py)     │     │  (conduct_research)
│    enabled)     │     └──────────────────┘     └─────────────────┘
└─────────────────┘                │                        │
                                   │◄───────────────────────┘
                                   │   Research context
                                   │
                          ┌────────▼─────────┐
                          │  ImageGenerator  │
                          │ (skills/image_   │
                          │   generator.py)  │
                          └────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────▼────────┐  ┌───────▼────────┐  ┌────────▼───────┐
    │ plan_and_generate│  │generate_images_│  │process_image_  │
    │   _images()      │  │  for_report()  │  │  placeholders()│
    └─────────┬────────┘  └───────┬────────┘  └────────┬───────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                          ┌────────▼─────────┐
                          │ Image Provider   │
                          │ (Google /        │
                          │  ModelsLab)      │
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │  outputs/images/ │
                          │  {research_id}/  │
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │ ReportGenerator  │
                          │ (skills/writer.py│
                          │  + generate_     │
                          │   report())      │
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │  Final Report    │
                          │ (with markdown   │
                          │   ![alt](url))   │
                          └──────────────────┘
```

---

## Step-by-Step Pipeline

### Step 0 — Initialization

When a `GPTResearcher` instance is created (`gpt_researcher/agent.py`):

1. `Config` loads settings from JSON file (if any) and environment variables.
2. `ImageGenerator(self)` is instantiated and stored on `self.image_generator`.
3. `ImageGenerator._init_provider()` checks `cfg.image_generation_enabled`.
   - If `false`, `self.image_provider` stays `None` and the feature is effectively a no-op.
   - If `true`, it instantiates either `ImageGeneratorProvider` (Google) or `ModelsLabImageGeneratorProvider` based on `cfg.image_generation_provider`.
4. The provider validates that the required API key is present (`is_available()`).

### Step 1 — Research

The user calls `await researcher.conduct_research()`.

- Normal web search, scraping, and context accumulation happens.
- If the report type is `deep_research`, the deep-research branch runs instead.

### Step 2 — Image Planning & Pre-Generation

Immediately after research completes (`agent.py`, inside `conduct_research()`):

```python
if self.image_generator and self.image_generator.is_enabled():
    context_str = "\n\n".join(self.context)
    self.available_images = await self.image_generator.plan_and_generate_images(
        context=context_str,
        query=self.query,
        research_id=self._generate_research_id(),
    )
```

**What happens inside `plan_and_generate_images`:**

1. **Concept Planning** (`_plan_image_concepts`)
   - Sends the first ~6,000 characters of research context + the original query to the **fast LLM** (`cfg.fast_llm_model`).
   - The LLM is instructed to return a JSON array of 2–3 visualization concepts, each with:
     - `title` — short descriptive name (e.g., "System Architecture Overview")
     - `prompt` — detailed image-generation prompt (≥30 words)
     - `section_hint` — which report section the image belongs to
   - Concepts are validated (must be a dict with `title` and `prompt`) and clipped to `max_images`.

2. **Parallel Generation**
   - For each concept, `image_provider.generate_image()` is called concurrently via `asyncio.gather()`.
   - The provider builds an **enhanced prompt** that injects style instructions (`dark`, `light`, or `auto`) and technical constraints (no text, no watermarks, professional infographic style).
   - The image is generated via the chosen provider API.
   - The returned image bytes are saved to disk.
   - A metadata dict is assembled:
     ```python
     {
       "path": "/absolute/path/to/img_abc123_0.png",
       "url": "/outputs/images/research_abc/img_abc123_0.png",
       "absolute_url": "/absolute/path/to/img_abc123_0.png",
       "prompt": "original prompt",
       "alt_text": "Illustration: original prompt...",
       "title": "Concept Title",
       "section_hint": "Architecture"
     }
     ```
   - The list of metadata dicts is stored on `self.available_images`.

### Step 3 — Report Writing

The user calls `await researcher.write_report()`.

1. `ReportGenerator.write_report()` receives `available_images=self.available_images`.
2. It passes them into `generate_report()` in `gpt_researcher/actions/report_generation.py`.
3. `generate_report()` appends an **image instruction block** to the LLM prompt:

   ```
   AVAILABLE IMAGES:
   You have the following pre-generated images available. Embed them in relevant
   sections of your report using the exact markdown syntax provided:

   - Image 1: ![System Architecture Overview](/outputs/images/.../img_abc123_0.png) - Architecture
   - Image 2: ![Process Flow](/outputs/images/.../img_def456_0.png) - Workflow

   Place each image on its own line after the relevant section header or paragraph.
   Use all available images where they add value to the content.
   ```

4. The smart LLM (`cfg.smart_llm_model`) writes the report, naturally inserting the images in appropriate sections.

### Step 4 — Alternative Flows (Not Always Used)

#### Post-Report Image Generation
If pre-generation was skipped or you want to retrofit images into an existing report:

```python
report, images = await image_generator.generate_images_for_report(report, query, research_id)
```

- The report is parsed into sections (`##` and `###` headers).
- Each section is sent to the fast LLM to score how much it would benefit from a visual.
- The top-scoring sections get images generated and inserted directly after their headers.

#### Placeholder Processing
If the report contains `[IMAGE: a diagram showing ...]` tags:

```python
report, images = await image_generator.process_image_placeholders(report, query, research_id)
```

- Regex finds all `[IMAGE: ...]` blocks.
- Each description is passed to the image provider.
- The tag is replaced with `\n\n![alt_text](url)\n\n`.
- If image generation is disabled, tags are stripped out.

### Step 5 — Output & Delivery

- The final report is a markdown string containing `![alt_text](/outputs/images/...)` image references.
- When converted to PDF/DOCX by the backend (`backend/utils.py`), the **absolute path** is used so the converter can read the image file.
- When displayed in the web frontend, the **web URL** (`/outputs/images/...`) is used; FastAPI serves the `outputs/` directory statically.

---

## Prompt Generation Deep Dive

### 1. Concept Planning Prompt

**File:** `gpt_researcher/skills/image_generator.py` (`_plan_image_concepts`)

The raw research context is truncated to 6,000 characters and wrapped in a system prompt that asks the fast LLM to act as a **visualization expert**. The LLM must return *only* a JSON array.

**Focus areas hard-coded into the prompt:**
- Architecture / system diagrams
- Process flows and workflows
- Comparison charts
- Data visualizations
- Conceptual illustrations

Example expected output:
```json
[
  {
    "title": "System Architecture Overview",
    "prompt": "A layered architecture diagram showing the frontend application on top, connecting to an API gateway in the middle, which routes to microservices at the bottom. Use clean boxes with connecting arrows, modern tech aesthetic.",
    "section_hint": "Architecture"
  }
]
```

### 2. Enhanced Image Prompt

**File:** `gpt_researcher/llm_provider/image/image_generator.py` (`_build_enhanced_prompt`)

Every base prompt is wrapped with style and technical requirements before hitting the provider API.

**Dark mode style** (default) instructs the model to produce:
- Dark background (`#0d1117` deep charcoal/navy)
- Primary accent: teal/cyan (`#14b8a6`, `#0d9488`)
- Secondary: slate grays + subtle purple
- Glowing, neon-like effects
- Modern, tech-forward, futuristic aesthetic
- High-contrast elements that pop

**Technical requirements appended to every prompt:**
- No text, labels, or watermarks in the image
- Clear visual hierarchy
- Well-balanced composition
- Suitable for digital viewing and printing
- Vector-style or clean photorealistic rendering
- Avoid cartoonish, cluttered, or generic stock-photo aesthetics

If `context` is provided, the last 300 characters are appended so the image model can ground the illustration in the research topic.

### 3. Report Analysis Prompt

**File:** `gpt_researcher/skills/image_generator.py` (`_build_analysis_prompt`)

Used only in the post-report generation flow. The prompt:
- Receives each report section (header + first 500 chars of content)
- Asks the LLM to return JSON with `suggestions` array
- Explicitly forbids images for introduction or conclusion sections
- Rates sections on: concepts, processes, comparisons, data flows, statistics

---

## Image Providers

### Google Provider (`ImageGeneratorProvider`)

**File:** `gpt_researcher/llm_provider/image/image_generator.py`

**Supported models:**

| Model | Tier | Notes |
|---|---|---|
| `models/gemini-2.5-flash-image` | Free | Default. Uses `generate_content` with inline image data. |
| `gemini-2.0-flash-exp-image-generation` | Free | Experimental image generation. |
| `gemini-3-pro-image-preview` | Free | Preview model. |
| `imagen-4.0-generate-001` | Paid | Uses `generate_images` API; supports `aspect_ratio`. |
| `imagen-4.0-fast-generate-001` | Paid | Faster paid variant. |
| `imagen-4.0-ultra-generate-001` | Paid | Higher quality paid variant. |

**Implementation details:**
- Uses the `google.genai` SDK (`genai.Client`).
- Gemini models return image data as `inline_data` inside response parts; the code extracts bytes and writes a PNG.
- Imagen models return `generated_images` with `image_bytes`; same write path.
- Square images from Gemini are kept as-is (landscape cropping code exists but is commented out).

### ModelsLab Provider (`ModelsLabImageGeneratorProvider`)

**File:** `gpt_researcher/llm_provider/image/modelslab_image_generator.py`

**Supported models:** Any ModelsLab text-to-image model ID (default: `flux`).

**Implementation details:**
- API endpoint: `POST https://modelslab.com/api/v6/images/text2img`
- Authentication: API key in JSON body (not Bearer token).
- Default payload:
  - `width: 768`, `height: 512`
  - `num_inference_steps: 30`
  - `guidance_scale: 7.5`
  - `safety_checker: yes`
  - `negative_prompt: "low quality, blurry, watermark, text, nsfw"`
- If the API returns `status: processing`, the provider polls `.../fetch/{id}` every 5 seconds up to 12 times (60-second max wait).
- Downloaded image bytes are saved to the same `outputs/images/{research_id}/` path.

---

## File System Layout

When an image is successfully generated, it is written to:

```
outputs/
└── images/
    └── {research_id}/          # e.g., research_a1b2c3d4e5f6
        ├── img_abc123_0.png
        ├── img_def456_0.png
        └── img_ghi789_0.png
```

If no `research_id` is supplied, images land directly in `outputs/images/`.

**Filename generation:**
```python
prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
filename = f"img_{prompt_hash}_{index}.png"
```

This guarantees a deterministic, collision-resistant name derived from the prompt content.

**Dual-path return values:**
Every provider returns a dict with two paths:
- `path` / `absolute_url` — absolute filesystem path (`Path.resolve()`), used by PDF/DOCX converters.
- `url` — web-relative path (`/outputs/images/...`), used by the frontend.

---

## Report Embedding

### Pre-Generated Images (Primary Flow)

1. `GPTResearcher.conduct_research()` stores images in `self.available_images`.
2. `GPTResearcher.write_report()` passes them to `ReportGenerator.write_report()`.
3. `ReportGenerator.write_report()` passes them to `generate_report()`.
4. `generate_report()` injects an `AVAILABLE IMAGES` instruction into the LLM prompt.
5. The smart LLM embeds images using exact markdown syntax, e.g.:
   ```markdown
   ## System Architecture

   ![System Architecture Overview](/outputs/images/research_abc/img_abc123_0.png)

   The system follows a layered approach...
   ```

### Post-Report Embedding

`ImageGenerator._embed_images_in_report()` scans the markdown line-by-line. When it encounters a header (`##` or `###`) that matches a section with a generated image, it inserts the markdown image immediately after the header line.

### Placeholder Replacement

`process_image_placeholders()` uses regex `\[IMAGE:\s*([^\]]+)\]` to find tags. Each match is replaced with `\n\n![alt_text](url)\n\n`. Failed generations are replaced with an empty string (tag removed).

### WebSocket Streaming

Throughout image generation, log events are streamed to the frontend via WebSocket:

| Event type | Message example |
|---|---|
| `image_planning` | "🎨 Analyzing research context for visualization opportunities..." |
| `image_concepts_identified` | "🖼️ Identified 3 visualization concepts, generating images..." |
| `image_generating` | "🖼️ Generating image 1/3: System Architecture..." |
| `images_ready` | "✅ 3 images ready for report embedding" |
| `generated_images` | JSON payload with `{url, alt}` array for real-time preview |

---

## Key Code References

| File | Responsibility |
|---|---|
| `gpt_researcher/agent.py` | Orchestrates research → image pre-generation → report writing. Instantiates `ImageGenerator`. |
| `gpt_researcher/skills/image_generator.py` | `ImageGenerator` class. Planning, generation, embedding, and placeholder processing. |
| `gpt_researcher/skills/writer.py` | `ReportGenerator`. Receives `available_images` and passes them to `generate_report()`. |
| `gpt_researcher/actions/report_generation.py` | `generate_report()`. Injects image instructions into the LLM prompt. |
| `gpt_researcher/llm_provider/image/image_generator.py` | `ImageGeneratorProvider` (Google Gemini/Imagen). |
| `gpt_researcher/llm_provider/image/modelslab_image_generator.py` | `ModelsLabImageGeneratorProvider`. |
| `gpt_researcher/config/config.py` | `Config` class. Loads env vars, casts types, exposes `cfg.image_generation_*`. |
| `gpt_researcher/config/variables/default.py` | Default values for all image settings. |
| `gpt_researcher/config/variables/base.py` | `BaseConfig` TypedDict with image key type annotations. |
| `gpt_researcher/prompts.py` | `PromptFamily` with helper methods for image-analysis prompts. |

---

## Pixabay Stock Photo Search

In addition to AI-generated images, GPT Researcher can search Pixabay for real stock photos that match the research topic. This runs as a parallel research step and adds found photos to the `research_images` collection.

### How It Works

1. **Query Generation** — After web research completes, the fast LLM analyzes the research context and generates 2–3 concise search queries optimized for Pixabay's photo search engine.
2. **Search & Download** — The `PixabayImageSearchProvider` queries the Pixabay API, selects the best result per query, and downloads the image locally.
3. **Attribution** — Each downloaded photo carries metadata including the photographer's name and Pixabay page URL.
4. **Delivery** — Photos are added to `research_images` and streamed to the frontend alongside scraped web images.

### Configuration

| Variable | Type | Default | Description |
|---|---|---|---|
| `PIXABAY_API_KEY` | str | `None` | Required. Get one at [pixabay.com/api/docs](https://pixabay.com/api/docs/). |
| `PIXABAY_IMAGE_SEARCH_ENABLED` | bool | `False` | Master switch. |
| `PIXABAY_MAX_IMAGES` | int | `3` | Max photos per report. |
| `PIXABAY_IMAGE_TYPE` | str | `"photo"` | `all`, `photo`, `illustration`, `vector`. |
| `PIXABAY_SAFESEARCH` | bool | `True` | Filter adult content. |
| `PIXABAY_SHOW_ATTRIBUTION` | bool | `True` | Include photographer credit. |
| `PIXABAY_MIN_WIDTH` / `PIXABAY_MIN_HEIGHT` | int | `800` / `600` | Minimum resolution. |

### Pixabay API Compliance

- **No hotlinking:** All images are downloaded to `outputs/images/pixabay/{research_id}/` immediately.
- **24-hour cache:** Local disk storage satisfies Pixabay's caching requirement.
- **Rate limits:** Built-in compliance (≤3 searches per report, well under the 100 req/60s limit).
- **Attribution:** Photographer name and page URL are included in image metadata.
- **SafeSearch:** Enabled by default.

### Key Code References for Pixabay

| File | Responsibility |
|---|---|
| `gpt_researcher/llm_provider/image/pixabay_image_search.py` | `PixabayImageSearchProvider`. Search, download, and metadata. |
| `gpt_researcher/agent.py` | `_generate_pixabay_search_queries()` and `_search_pixabay_images()` — LLM-driven query generation and orchestration. |
| `IMAGE_CREDENTIALS.md` | Documentation for all image-provider API keys. |

---

## Pexels Stock Photo Search

GPT Researcher can also search Pexels for high-quality stock photos. Like Pixabay, this runs as a parallel research step and adds found photos to the `research_images` collection.

### How It Works

1. **Query Generation** — The fast LLM analyzes research context and generates 2–3 concise search queries.
2. **Search & Download** — The `PexelsImageSearchProvider` queries the Pexels API, selects the best photo per query, and downloads the image locally.
3. **Attribution** — Each photo carries metadata including the photographer's name and Pexels page URL.
4. **Delivery** — Photos are added to `research_images` and streamed to the frontend.

### Configuration

| Variable | Type | Default | Description |
|---|---|---|---|
| `PEXELS_API_KEY` | str | `None` | Required. Get one at [pexels.com/api](https://www.pexels.com/api/). |
| `PEXELS_IMAGE_SEARCH_ENABLED` | bool | `False` | Master switch. |
| `PEXELS_MAX_IMAGES` | int | `3` | Max photos per report. |
| `PEXELS_SHOW_ATTRIBUTION` | bool | `True` | Include photographer credit. |

### Pexels API Compliance

- **Attribution:** Photographer name and Pexels page URL included in metadata.
- **Rate limits:** Built-in compliance (≤3 searches per report, well under 200 req/hour).
- **Auth:** Header-based `Authorization` sent with every request.

### Key Code References for Pexels

| File | Responsibility |
|---|---|
| `gpt_researcher/llm_provider/image/pexels_image_search.py` | `PexelsImageSearchProvider`. Search, download, and metadata. |
| `gpt_researcher/agent.py` | `_search_pexels_images()` — orchestrates LLM query generation and Pexels search. |

---

## Unsplash Stock Photo Search

GPT Researcher can also search Unsplash for high-quality editorial-style photos. Unsplash runs as a parallel research step and adds found photos to the `research_images` collection.

### How It Works

1. **Query Generation** — The fast LLM analyzes research context and generates 2–3 concise search queries.
2. **Search** — The `UnsplashImageSearchProvider` queries the Unsplash API and selects the best photo per query.
3. **Hotlinking** — Unsplash requires serving images directly from their CDN. URLs are returned as-is; images are **not** downloaded locally.
4. **Attribution** — Each photo carries metadata including the photographer's name and Unsplash page URL.
5. **Delivery** — Photos are added to `research_images` and streamed to the frontend.

### Configuration

| Variable | Type | Default | Description |
|---|---|---|---|
| `UNSPLASH_ACCESS_KEY` | str | `None` | Required. Get one at [unsplash.com/developers](https://unsplash.com/developers). |
| `UNSPLASH_IMAGE_SEARCH_ENABLED` | bool | `False` | Master switch. |
| `UNSPLASH_MAX_IMAGES` | int | `3` | Max photos per report. |
| `UNSPLASH_SHOW_ATTRIBUTION` | bool | `True` | Include photographer credit. |

### Unsplash API Compliance

- **Hotlinking required:** Images are served directly from `images.unsplash.com` CDN. No local downloads.
- **Attribution:** Photographer name and Unsplash link included in metadata.
- **Rate limits:** Built-in compliance (≤3 searches per report, well under 50 req/hour demo limit).
- **Auth:** `Authorization: Client-ID YOUR_ACCESS_KEY` header sent with every request.
- **ixid preserved:** The `ixid` tracking parameter is kept intact on all returned URLs.

### Key Code References for Unsplash

| File | Responsibility |
|---|---|
| `gpt_researcher/llm_provider/image/unsplash_image_search.py` | `UnsplashImageSearchProvider`. Search and metadata (no download — hotlinked CDN URLs). |
| `gpt_researcher/agent.py` | `_search_unsplash_images()` — orchestrates LLM query generation and Unsplash search. |

---

## Summary

1. **Enable** the feature in `.env` (`IMAGE_GENERATION_ENABLED=true`) and provide the correct API key.
2. **Research** runs as normal; context is accumulated.
3. **Plan** — the fast LLM analyzes context and proposes 2–3 visualization concepts.
4. **Generate** — the image provider (Google or ModelsLab) creates images in parallel, saving them to `outputs/images/{research_id}/`.
5. **Write** — the report LLM is told which images exist and embeds them as markdown.
6. **Deliver** — the final report contains `![alt](url)` references that work both in the web UI and in exported PDF/DOCX files.

**Pixabay addition:** Enable `PIXABAY_IMAGE_SEARCH_ENABLED=true` with a `PIXABAY_API_KEY` to also fetch real stock photos during research. Photos are downloaded locally, attributed, and added to the research image collection.
