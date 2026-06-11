# Image Provider Credentials Guide

> This document lists all API keys and credentials required for image-related features in GPT Researcher. Keep these values in your `.env` file or environment variables — never commit them to version control.

---

## Table of Contents

1. [Google / Gemini](#google--gemini)
2. [ModelsLab](#modelslab)
3. [Pixabay](#pixabay)
4. [Pexels](#pexels)

---

## Google / Gemini

**Used for:** AI-generated images via `IMAGE_GENERATION_PROVIDER=google`

| Variable | Required | How to Obtain |
|---|---|---|
| `GOOGLE_API_KEY` | **Yes** (if using Google) | [Google AI Studio](https://aistudio.google.com/app/apikey) or Google Cloud Console |
| `GEMINI_API_KEY` | Alternative to `GOOGLE_API_KEY` | Same as above; either variable is accepted |

**Free tier models:**
- `models/gemini-2.5-flash-image`
- `gemini-2.0-flash-exp-image-generation`

**Paid tier models:**
- `imagen-4.0-generate-001`
- `imagen-4.0-fast-generate-001`
- `imagen-4.0-ultra-generate-001`

---

## ModelsLab

**Used for:** AI-generated images via `IMAGE_GENERATION_PROVIDER=modelslab`

| Variable | Required | How to Obtain |
|---|---|---|
| `MODELSLAB_API_KEY` | **Yes** (if using ModelsLab) | [modelslab.com/account/api-key](https://modelslab.com/account/api-key) |

**Supported models:** Any ModelsLab text-to-image model ID. Default: `flux`

---

## Pixabay

**Used for:** Stock photo search via `PIXABAY_IMAGE_SEARCH_ENABLED=true`

| Variable | Required | How to Obtain |
|---|---|---|
| `PIXABAY_API_KEY` | **Yes** (if using Pixabay) | [pixabay.com/api/docs](https://pixabay.com/api/docs/) — free registration |

**What Pixabay provides:**
- Royalty-free stock photos, illustrations, and vector graphics
- No attribution required for downloaded images (but appreciated)
- Commercial use allowed

**Pixabay API Rules (mandatory compliance):**
1. **Rate limit:** 100 requests per 60 seconds
2. **Caching:** Requests must be cached for 24 hours
3. **No hotlinking:** Images must be downloaded to your own server; Pixabay URLs cannot be used directly in your app permanently
4. **Attribution:** Show users where images come from when displaying search results
5. **SafeSearch:** Adult content is filtered by default (`PIXABAY_SAFESEARCH=true`)

**Related configuration variables:**
- `PIXABAY_IMAGE_SEARCH_ENABLED` — Master on/off switch
- `PIXABAY_MAX_IMAGES` — Max photos per report (default: 3)
- `PIXABAY_IMAGE_TYPE` — `photo`, `illustration`, `vector`, or `all`
- `PIXABAY_SAFESEARCH` — Filter adult content (default: `true`)
- `PIXABAY_SHOW_ATTRIBUTION` — Include photographer credit in metadata (default: `true`)
- `PIXABAY_MIN_WIDTH` / `PIXABAY_MIN_HEIGHT` — Minimum resolution filters

---

## Pexels

**Used for:** Stock photo search via `PEXELS_IMAGE_SEARCH_ENABLED=true`

| Variable | Required | How to Obtain |
|---|---|---|
| `PEXELS_API_KEY` | **Yes** (if using Pexels) | [pexels.com/api](https://www.pexels.com/api/) — free registration |

**What Pexels provides:**
- High-quality stock photos and videos
- Free to use under the Pexels license
- Commercial use allowed

**Pexels API Rules (mandatory compliance):**
1. **Rate limit:** 200 requests/hour, 20,000 requests/month (default)
2. **Attribution:** You **must** display a prominent link to Pexels. You **should** credit photographers when possible.
3. **Auth:** Header-based (`Authorization: YOUR_API_KEY`)

**Related configuration variables:**
- `PEXELS_IMAGE_SEARCH_ENABLED` — Master on/off switch
- `PEXELS_MAX_IMAGES` — Max photos per report (default: 3)
- `PEXELS_SHOW_ATTRIBUTION` — Include photographer credit in metadata (default: `true`)

---

## Unsplash

**Used for:** Stock photo search via `UNSPLASH_IMAGE_SEARCH_ENABLED=true`

| Variable | Required | How to Obtain |
|---|---|---|
| `UNSPLASH_ACCESS_KEY` | **Yes** (if using Unsplash) | [unsplash.com/developers](https://unsplash.com/developers) — free registration |

**What Unsplash provides:**
- High-quality editorial-style stock photos
- Free to use under the Unsplash license
- Commercial use allowed

**Unsplash API Rules (mandatory compliance):**
1. **Rate limit:** 50 requests/hour (demo), 1,000 requests/hour (production approved)
2. **Attribution:** You **must** credit the photographer and Unsplash
3. **Hotlinking REQUIRED:** You must use Unsplash CDN URLs directly. Do NOT download or re-host images.
4. **Auth:** Header-based (`Authorization: Client-ID YOUR_ACCESS_KEY`)
5. **Preserve `ixid` parameter:** Must be kept intact on all image URLs for tracking

**Related configuration variables:**
- `UNSPLASH_IMAGE_SEARCH_ENABLED` — Master on/off switch
- `UNSPLASH_MAX_IMAGES` — Max photos per report (default: 3)
- `UNSPLASH_SHOW_ATTRIBUTION` — Include photographer credit in metadata (default: `true`)

---

## Security Notes

- **Never commit API keys** to Git. Use `.env` files or secret managers.
- The `.env.example` file in this repo contains placeholder keys only.
- All keys are read at runtime by the `Config` class in `gpt_researcher/config/config.py`.
- If a key is missing, the corresponding feature gracefully disables itself with a warning log.
