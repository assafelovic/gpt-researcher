# Configuration Reference

## Table of Contents
- [Required Variables](#required-variables)
- [LLM Configuration](#llm-configuration)
- [Provider API Keys](#provider-api-keys)
- [Retriever Configuration](#retriever-configuration)
- [Report Configuration](#report-configuration)
- [Feature Toggles](#feature-toggles)
- [Configuration Priority](#configuration-priority)
- [Example .env](#example-env)

---

## Required Variables

```bash
OPENAI_API_KEY=sk-...          # Or another LLM provider key
TAVILY_API_KEY=tvly-...        # Or another retriever key
```

---

## LLM Configuration

```bash
LLM_PROVIDER=openai            # openai, anthropic, google, groq, together, etc.
FAST_LLM=gpt-4o-mini           # Quick tasks (summarization)
SMART_LLM=gpt-4o               # Complex reasoning (report writing)
STRATEGIC_LLM=o3-mini          # Planning (agent selection)
TEMPERATURE=0.4                # 0.0-1.0
MAX_TOKENS=4000
REASONING_EFFORT=medium        # For o-series: low, medium, high
```

---

## Provider API Keys

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GOOGLE_API_KEY=AIza...

# Groq
GROQ_API_KEY=gsk_...

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

---

## Retriever Configuration

```bash
RETRIEVER=tavily               # Single or comma-separated: tavily,google,mcp
MAX_SEARCH_RESULTS_PER_QUERY=5
MAX_URLS_TO_SCRAPE=10
SIMILARITY_THRESHOLD=0.42
```

### Retriever API Keys

```bash
TAVILY_API_KEY=tvly-...
GOOGLE_API_KEY=AIza...
GOOGLE_CX_KEY=...
BING_API_KEY=...
SERPER_API_KEY=...
SERPAPI_API_KEY=...
EXA_API_KEY=...
```

---

## Report Configuration

```bash
REPORT_FORMAT=apa              # apa, mla, chicago, harvard, ieee
TOTAL_WORDS=1000
LANGUAGE=english
CURATE_SOURCES=true
```

---

## Feature Toggles

### Image Generation

```bash
IMAGE_GENERATION_ENABLED=true
GOOGLE_API_KEY=AIza...
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image
IMAGE_GENERATION_MAX_IMAGES=3
IMAGE_GENERATION_STYLE=dark    # dark, light, auto
```

### Deep Research

```bash
DEEP_RESEARCH_BREADTH=4        # Subtopics per level
DEEP_RESEARCH_DEPTH=2          # Recursion levels
DEEP_RESEARCH_CONCURRENCY=2    # Parallel tasks
```

### MCP

```bash
MCP_STRATEGY=fast              # fast, deep, disabled
```

### Local Documents

```bash
DOC_PATH=./my-docs
# Supports: PDF, DOCX, TXT, CSV, XLSX, PPTX, MD
```

### Server

```bash
HOST=0.0.0.0
PORT=8000
VERBOSE=true
```

---

## Configuration Priority

```
Environment Variables (highest)
        ↓
JSON Config File (if provided)
        ↓
Default Values (lowest)
```

**Important:** Config keys are lowercased when accessed:

```python
# In default.py: "SMART_LLM": "gpt-4o"
# Access as: self.cfg.smart_llm  # lowercase!
```

---

## Example .env

```bash
# Required
OPENAI_API_KEY=sk-your-key
TAVILY_API_KEY=tvly-your-key

# LLM
FAST_LLM=gpt-4o-mini
SMART_LLM=gpt-4o

# Report
TOTAL_WORDS=1000
LANGUAGE=english

# Optional: Images
IMAGE_GENERATION_ENABLED=true
GOOGLE_API_KEY=AIza-your-key
IMAGE_GENERATION_STYLE=dark
```
