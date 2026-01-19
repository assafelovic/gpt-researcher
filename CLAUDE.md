# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference Commands

```bash
# Start FastAPI server (main entry point)
python -m uvicorn main:app --reload

# Or run directly
python main.py

# Run Python tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_mcp.py

# Run multi-agent system
cd multi_agents && python main.py

# Docker (starts backend on :8000, NextJS on :3000)
docker-compose up --build

# Run tests in Docker
docker-compose run gpt-researcher-tests

# NextJS frontend (separate terminal)
cd frontend/nextjs && npm install && npm run dev
```

## Architecture Overview

### Core Research Engine (`gpt_researcher/`)

The `GPTResearcher` class (`agent.py`) is the main orchestrator that coordinates research through specialized skills:

- **skills/researcher.py** - `ResearchConductor`: Conducts research by generating questions and gathering information
- **skills/writer.py** - `ReportGenerator`: Compiles findings into structured reports
- **skills/browser.py** - `BrowserManager`: Handles web scraping and content extraction
- **skills/curator.py** - `SourceCurator`: Validates and filters research sources
- **skills/context_manager.py** - `ContextManager`: Maintains research context across iterations
- **skills/deep_research.py** - `DeepResearchSkill`: Tree-like recursive research with configurable depth/breadth

Research flow: Query → Agent Selection → Question Generation → Parallel Scraping → Summarization → Report Generation

### Retrievers (`gpt_researcher/retrievers/`)

Search backends that find sources: `tavily`, `duckduckgo`, `google`, `bing`, `arxiv`, `exa`, `serper`, `serpapi`, `searchapi`, `searx`, `semantic_scholar`, `pubmed_central`, `mcp` (Model Context Protocol), `custom`

Set via `RETRIEVER` env var (comma-separated for multiple): `export RETRIEVER=tavily,mcp`

### Multi-Agent System (`multi_agents/`)

LangGraph-based workflow with specialized agents:
- **orchestrator.py** - Coordinates the research pipeline using LangGraph
- **editor.py** - Plans report outline and structure
- **researcher.py** - Wraps GPTResearcher for subtopic research
- **reviewer.py** - Validates research correctness
- **reviser.py** - Revises based on reviewer feedback
- **writer.py** - Compiles final report
- **publisher.py** - Outputs to PDF, DOCX, Markdown

Configure research task in `multi_agents/task.json`.

### Backend Server (`backend/`)

FastAPI application serving:
- **server/app.py** - Main FastAPI app with REST and WebSocket endpoints
- **server/websocket_manager.py** - Real-time research progress streaming
- **chat/** - Chat agent with memory for conversational research
- **report_type/** - Report type handlers
- **utils.py** - PDF/DOCX export utilities

### Frontend (`frontend/`)

Two options:
1. **Lightweight** - Static HTML/JS served by FastAPI (`frontend/index.html`)
2. **Production** - NextJS + Tailwind (`frontend/nextjs/`)

NextJS commands: `npm run dev`, `npm run build`, `npm run lint`

## Key Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=           # Or other LLM provider key
TAVILY_API_KEY=           # Default search retriever

# LLM Configuration (format: provider:model)
FAST_LLM=openai:gpt-4o-mini        # Quick tasks
SMART_LLM=openai:gpt-4.1           # Complex reasoning
STRATEGIC_LLM=openai:o4-mini       # Planning tasks

# Embedding
EMBEDDING=openai:text-embedding-3-small

# Research Sources
RETRIEVER=tavily                   # Comma-separated: tavily,duckduckgo
REPORT_SOURCE=web                  # web, local, hybrid
DOC_PATH=./my-docs                 # For local document research

# Scraper settings
SCRAPER=bs                         # bs, browser, firecrawl
MAX_SCRAPER_WORKERS=15
SCRAPER_RATE_LIMIT_DELAY=0.0       # Seconds between requests
```

### Config System (`gpt_researcher/config/`)

- `config.py` - Main Config class that merges defaults with env vars
- `variables/default.py` - Default configuration values
- `variables/base.py` - Type definitions

## Code Style Guidelines

- TypeScript strict mode for frontend code
- Follow ESLint/Prettier configurations
- Python: Use type hints, async/await patterns
- Minimize comments; prefer self-documenting code
- Use existing components/patterns as reference implementations
