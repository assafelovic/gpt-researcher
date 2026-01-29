# Inline Image Generation

GPT Researcher now supports **inline image generation** for research reports using Google's Gemini image generation models (Nano Banana). This feature creates contextually relevant illustrations embedded directly within your research reports.

## Overview

When enabled, GPT Researcher will:
1. Analyze your completed research report to identify sections that would benefit from visual illustrations
2. Generate professional images using AI for the most impactful sections
3. Automatically embed the images inline within the markdown report

## Configuration

### Environment Variables

To enable image generation, set the following environment variables:

```bash
# Required: Enable the feature
IMAGE_GENERATION_ENABLED=true

# Required: Specify the model to use
IMAGE_GENERATION_MODEL=gemini-2.0-flash-preview-image-generation

# Required: Your Google API key
GOOGLE_API_KEY=your_google_api_key_here
# Or alternatively:
GEMINI_API_KEY=your_google_api_key_here

# Optional: Maximum images per report (default: 3)
IMAGE_GENERATION_MAX_IMAGES=3
```

### Supported Models

The following image generation models are supported:

| Model | Description |
|-------|-------------|
| `gemini-2.0-flash-preview-image-generation` | Fast, efficient model for quick generation |
| `gemini-2.0-flash-exp-image-generation` | Experimental Gemini Flash with image capabilities |
| `imagen-3.0-generate-002` | Google's Imagen 3 model (latest) |
| `imagen-3.0-generate-001` | Google's Imagen 3 model |

## Usage

### Python API

```python
import os
from gpt_researcher import GPTResearcher

# Enable image generation via environment
os.environ["IMAGE_GENERATION_ENABLED"] = "true"
os.environ["IMAGE_GENERATION_MODEL"] = "gemini-2.0-flash-preview-image-generation"
os.environ["GOOGLE_API_KEY"] = "your_api_key"

# Create researcher
researcher = GPTResearcher(
    query="What are the key components of a modern solar panel system?",
    report_type="research_report"
)

# Conduct research
await researcher.conduct_research()

# Generate report with inline images
report = await researcher.write_report(
    generate_images=True,  # Enable image generation (default is True if configured)
    research_id="solar_panels_research"  # Optional: organize output files
)

print(report)  # Report now contains inline markdown images
```

### Disabling for Specific Reports

If image generation is enabled globally but you want to skip it for a specific report:

```python
# Generate report without images
report = await researcher.write_report(generate_images=False)
```

## How It Works

1. **Report Analysis**: After the report is written, GPT Researcher uses an LLM to analyze the content and identify 2-3 sections that would most benefit from visual illustrations.

2. **Image Prompt Generation**: For each identified section, a detailed, context-aware image prompt is generated based on the section content.

3. **Image Generation**: The prompts are sent to the Gemini image generation API, which returns professional illustrations.

4. **Embedding**: Generated images are saved locally and embedded as markdown images in the report.

## Output

Generated images are saved to:
```
outputs/images/{research_id}/generated_{hash}_{index}.png
```

The images are embedded in the markdown using standard syntax:
```markdown
## Section Title

![Illustration: Description of the image](outputs/images/research_id/generated_abc123_0.png)

The section content continues here...
```

## WebSocket Events

When using the web interface, the following events are emitted during image generation:

| Event | Content | Description |
|-------|---------|-------------|
| `image_generation_start` | Log message | Image analysis beginning |
| `image_generation_analyzing` | Log message | Sections identified |
| `image_generating` | Log message | Generating each image |
| `image_generated` | Log message | Individual image completed |
| `image_generation_complete` | Log message | All images done |
| `generated_images` | Image list | Final generated image URLs |

## Best Practices

1. **Choose Report Types Wisely**: Image generation works best with `research_report` and `detailed_report` types. It's automatically skipped for outline and resource reports.

2. **API Costs**: Be aware that image generation incurs additional API costs. Consider setting `IMAGE_GENERATION_MAX_IMAGES` to control expenses.

3. **Report Quality**: Longer, more detailed reports with clear sections tend to produce better image suggestions.

4. **Review Generated Images**: AI-generated images may occasionally require manual review for accuracy.

## Troubleshooting

### Images Not Generating

1. Verify `IMAGE_GENERATION_ENABLED=true` is set
2. Check that `GOOGLE_API_KEY` or `GEMINI_API_KEY` is valid
3. Ensure the model name is correct
4. Check logs for API errors

### API Errors

If you see quota or rate limit errors:
- Reduce `IMAGE_GENERATION_MAX_IMAGES`
- Use a different model (Flash models are faster and cheaper)
- Check your Google Cloud project quotas

### Images Not Displaying

1. Ensure the `outputs/images/` directory is accessible
2. For web interface, verify the frontend can serve static files from outputs
3. Check image paths in the generated markdown
