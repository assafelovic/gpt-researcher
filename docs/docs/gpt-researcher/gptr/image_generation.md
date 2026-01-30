---
sidebar_label: Image Generation
sidebar_position: 5
---

# 🍌 Inline Image Generation

GPT Researcher supports **inline image generation** for research reports using Google's Gemini image generation models (Nano Banana). This feature creates contextually relevant illustrations that are embedded directly within your research reports.

## Overview

When enabled, GPT Researcher will:
1. **Analyze research context** after gathering information to identify visualization opportunities
2. **Pre-generate images** before writing the report (for seamless UX)
3. **Embed images inline** as the report is written - no post-processing delays!

## Quick Start

### 1. Set Environment Variables

```bash
# Required: Enable the feature
IMAGE_GENERATION_ENABLED=true

# Required: Your Google API key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Specify the model (default shown)
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image

# Optional: Maximum images per report (default: 3)
IMAGE_GENERATION_MAX_IMAGES=3

# Optional: Image style - "dark" (default), "light", or "auto"
IMAGE_GENERATION_STYLE=dark
```

### 2. Run Research

```python
import asyncio
from gpt_researcher import GPTResearcher

async def main():
    researcher = GPTResearcher(
        query="What are the key components of a modern solar panel system?",
        report_type="research_report"
    )
    
    # Images are automatically generated during research
    await researcher.conduct_research()
    
    # Report includes embedded images
    report = await researcher.write_report()
    print(report)

asyncio.run(main())
```

That's it! Images will be automatically generated and embedded in your report.

## How It Works

### The Smart Pre-Generation Flow

```
Research Phase          Image Planning          Report Writing
     │                       │                       │
     ▼                       ▼                       ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│ Gather      │      │ LLM analyzes │      │ Report streams  │
│ information │  →   │ context for  │  →   │ with images     │
│ from sources│      │ 2-3 visuals  │      │ already inline! │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Generate all │
                     │ images in    │
                     │ parallel     │
                     └──────────────┘
```

**Key benefits:**
- **No waiting** - Images are generated during research, not after
- **Seamless UX** - Report streams with images already embedded
- **Context-aware** - LLM chooses the best visualization opportunities

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_GENERATION_ENABLED` | `false` | Master switch to enable/disable |
| `GOOGLE_API_KEY` | - | Your Google API key (required) |
| `IMAGE_GENERATION_MODEL` | `models/gemini-2.5-flash-image` | Gemini model to use |
| `IMAGE_GENERATION_MAX_IMAGES` | `3` | Maximum images per report |
| `IMAGE_GENERATION_STYLE` | `dark` | Image style: `dark`, `light`, `auto` |

### Supported Models

**Free Tier (Gemini):**
| Model | Description |
|-------|-------------|
| `models/gemini-2.5-flash-image` | Recommended - fast and free |
| `gemini-2.0-flash-exp-image-generation` | Experimental variant |

**Paid Tier (Imagen) - requires Google Cloud billing:**
| Model | Description |
|-------|-------------|
| `imagen-4.0-generate-001` | Highest quality, supports aspect ratios |
| `imagen-4.0-fast-generate-001` | Faster generation |

## Image Styling

### Dark Mode (Default)

Images are generated with styling that matches the GPT Researcher UI:
- Dark background (`#0d1117`)
- Teal/cyan accents (`#14b8a6`)
- Glowing, futuristic aesthetic
- Professional infographic style

### Light Mode

Set `IMAGE_GENERATION_STYLE=light` for:
- Clean white/light gray backgrounds
- Deep blue and teal accents
- Corporate/professional aesthetic

### Auto Mode

Set `IMAGE_GENERATION_STYLE=auto` for neutral styling that works in any context.

## Output

### Image Storage

Generated images are saved to:
```
outputs/images/{research_id}/img_{hash}_{index}.png
```

### Markdown Embedding

Images are embedded using standard markdown syntax:
```markdown
## System Architecture

![System Architecture Overview](/outputs/images/research_abc123/img_def456_0.png)

The architecture consists of three main components...
```

### Frontend Display

For the Next.js frontend, images are served via the `/outputs/` route which proxies to the backend. Images display at 75% width with teal accent borders.

## WebSocket Events

When using the web interface, these events are emitted:

| Event | Description |
|-------|-------------|
| `image_planning` | Analyzing context for visuals |
| `image_concepts_identified` | Found N visualization opportunities |
| `image_generating` | Generating image X of Y |
| `images_ready` | All images generated successfully |

## Best Practices

1. **Enable for detailed reports** - Works best with `research_report` and `detailed_report` types

2. **Monitor API usage** - Free tier has daily quotas. Set `IMAGE_GENERATION_MAX_IMAGES=2` to conserve

3. **Use dark mode** - Default styling matches the app and looks professional

4. **Review generated images** - AI images occasionally need manual review

## Troubleshooting

### Images Not Generating

1. Verify `IMAGE_GENERATION_ENABLED=true`
2. Check that `GOOGLE_API_KEY` is set and valid
3. Ensure model name is correct (include `models/` prefix for Gemini)
4. Check logs for API errors

### Quota Exceeded

If you see `RESOURCE_EXHAUSTED` errors:
- Wait until midnight UTC for daily quota reset
- Reduce `IMAGE_GENERATION_MAX_IMAGES`
- Enable Google Cloud billing for higher quotas
- Create a new Google Cloud project for fresh quota

### Images Not Displaying in Frontend

1. Ensure Next.js frontend is configured with the `/outputs` proxy
2. Check that backend is serving static files from `outputs/`
3. Verify image paths in the markdown are correct

## Disabling Image Generation

To disable completely:
```bash
IMAGE_GENERATION_ENABLED=false
```

Or simply don't set any `IMAGE_GENERATION_*` variables - the feature is off by default.
