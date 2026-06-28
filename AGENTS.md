# GPT Researcher — Agent Guide

> This file is maintained for AI coding agents. It describes the project architecture, build/test workflows, and conventions you must follow when modifying code.

---

## Project Overview

**GPT Researcher** is an autonomous deep-research agent that conducts comprehensive online and local research on any topic and generates detailed, cited reports. It can be used as a Python library, a CLI tool, a FastAPI web service, or a multi-agent LangGraph/AG2 system.

- **Primary language**: Python 3.11+ (backend/core), TypeScript/React (frontend)
- **Web framework**: FastAPI + Uvicorn
- **Agent framework**: LangChain / LangGraph
- **Default LLM**: OpenAI (`gpt-4o-mini` for fast, `gpt-4.1` for smart, `o4-mini` for strategic)
- **Default retriever**: Tavily (web search)
- **License**: MIT
- **Repository**: https://github.com/assafelovic/gpt-researcher

---

## Technology Stack

### Backend / Core
- **FastAPI** — REST API and WebSocket server
- **Uvicorn** — ASGI server
- **Pydantic v2** — Request/response validation and settings
- **LangChain v1 + LangGraph** — LLM chains, agent orchestration, and multi-agent graphs
- **LiteLLM** — Unified interface for multiple LLM providers
- **OpenAI / Ollama / Anthropic / Google / Groq / Mistral / etc.** — Supported LLM providers via LiteLLM and LangChain adapters
- **SQLAlchemy** — Lightweight ORM usage
- **Loguru + standard logging** — Application logging

### Search & Retrieval
- **Tavily** — Primary web search and extract API
- **DuckDuckGo, Bing, Google, Arxiv, Exa, PubMed Central, OpenAlex, Bocha, SearchAPI** — Alternative retrievers (see `gpt_researcher/retrievers/`)
- **MCP (Model Context Protocol)** — Connects to external data sources (GitHub, DBs, custom APIs)

### Scraping & Document Processing
- **BeautifulSoup4** — Default HTML scraper
- **Browser/Selenium + Playwright + nodriver** — JavaScript-enabled scraping
- **Firecrawl, Tavily Extract** — Managed scraping services
- **Unstructured, PyMuPDF, python-docx, python-pptx, pandas** — Local document parsing
- **Markdown, mistune, md2pdf, htmldocx, WeasyPrint** — Report output formatting

### Frontend
- **Static version** — HTML/CSS/JS served directly by FastAPI from `frontend/`
- **Next.js 14 + TypeScript + Tailwind CSS** — Production frontend in `frontend/nextjs/`

### DevOps
- **Docker + Docker Compose** — Containerization (multi-stage Dockerfile with Chromium/Firefox)
- **Terraform** — AWS infrastructure (ECR, ECS/Fargate-style deployment)
- **GitHub Actions** — Build, push to ECR, deploy, and Docker-based tests

---

## Repository Layout

```
gpt-researcher/
├── gpt_researcher/           # Core research agent package (published to PyPI)
│   ├── actions/              # Agent creation, query processing, report generation, retriever mgmt, web scraping
│   ├── config/               # Configuration loader + default variables
│   ├── context/              # Context compression and retriever helpers
│   ├── document/             # Document loaders (local, Azure, LangChain, online)
│   ├── llm_provider/         # Generic LLM provider + image generation
│   ├── memory/               # Embeddings wrapper
│   ├── mcp/                  # MCP client, research integration, streaming, tool selection
│   ├── retrievers/           # One directory per search backend (tavily, duckduckgo, bing, google, arxiv, exa, mcp, ...)
│   ├── scraper/              # Scraping backends (bs, browser, firecrawl, tavily_extract, pymupdf, arxiv, web_base_loader)
│   ├── skills/               # Core agent skills: browser, context_manager, curator, deep_research, image_generator, researcher, writer
│   ├── utils/                # Enums (ReportType, ReportSource, Tone, PromptFamily), LLM helpers, etc.
│   ├── agent.py              # Main GPTResearcher class
│   ├── prompts.py            # Prompt templates
│   └── vector_store.py       # Vector store wrapper
├── backend/                  # FastAPI server and report orchestration
│   ├── chat/                 # Chat agent with memory
│   ├── memory/               # Draft and research memory utilities
│   ├── report_type/          # Report orchestrators: basic_report, detailed_report, deep_research
│   ├── server/               # FastAPI app, websocket manager, report store, agent discovery, multi-agent runner
│   ├── run_server.py         # Legacy server entrypoint
│   └── utils.py              # File writing helpers (MD, PDF, DOCX)
├── frontend/                 # User interfaces
│   ├── index.html            # Lightweight static frontend
│   ├── scripts.js / styles.css
│   └── nextjs/               # Production Next.js 14 app (pages under app/, API routes, components)
├── multi_agents/             # LangGraph-based multi-agent research system
│   ├── agents/               # editor, human, orchestrator, plan_review, publisher, researcher, reviewer, reviser, writer
│   ├── memory/               # Draft and research memory
│   ├── main.py               # Entrypoint
│   └── requirements.txt      # Extra deps: langgraph, weasyprint, etc.
├── multi_agents_ag2/         # AG2 (AutoGen) based multi-agent system
│   └── requirements.txt      # ag2[openai]
├── tests/                    # Test suite
├── docs/                     # Docusaurus documentation site
├── terraform/                # AWS Terraform modules
├── cli.py                    # Command-line interface entrypoint
├── main.py                   # FastAPI entrypoint (runs uvicorn)
├── pyproject.toml            # Poetry/uv project config + pytest settings
├── requirements.txt          # Primary Python dependencies
└── setup.py                  # setuptools fallback for pip installs
```

---

## Build and Run Commands

### Local Development (Backend)

```bash
# 1. Install Python 3.11+ and create a virtual environment
# 2. Install dependencies
pip install -r requirements.txt

# 3. Set required API keys
export OPENAI_API_KEY="sk-..."
export TAVILY_API_KEY="tvly-..."

# 4. Start the FastAPI server with hot reload
python -m uvicorn main:app --reload
# Server runs on http://localhost:8000
# Static frontend is served at /site
```

### CLI Usage

```bash
python cli.py "why is Nvidia stock going up?" --report_type research_report --tone objective

# Available report types: research_report, detailed_report, resource_report, outline_report, custom_report, subtopic_report, deep
# Available tones: objective, formal, analytical, persuasive, informative, explanatory, descriptive, critical, comparative, speculative, reflective, narrative, humorous, optimistic, pessimistic
```

### Frontend Development

```bash
# Static frontend is auto-served by FastAPI from frontend/

# Next.js development (production UI)
cd frontend/nextjs
npm install
npm run dev        # localhost:3000
npm run build      # production build
npm run lint       # ESLint
```

### Docker

```bash
# Copy environment template and fill in keys
cp .env.example .env

# Build and run both backend (port 8000) and Next.js frontend (port 3000)
docker-compose up --build

# Run tests inside Docker
docker-compose --profile test run --rm gpt-researcher-tests
```

### Install as a Library

```bash
pip install gpt-researcher
```

---

## Testing Instructions

### Test Framework
- **pytest** with `asyncio_mode = strict`
- Configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`
- Test discovery: `testpaths = ["tests"]`, `python_files = "test_*.py"`

### Running Tests

```bash
# Run all tests that match standard naming
pytest

# Some test files do NOT follow the `test_*.py` naming convention.
# To run those explicitly:
python -m pytest tests/report-types.py
python -m pytest tests/vector-store.py
```

### Test Categories
- **Unit/integration**: `tests/report-types.py`, `tests/test_research_conductor_retrieval.py`, `tests/test_websocket_manager.py`, `tests/test_llm_max_tokens.py`, `tests/test_costs.py`, etc.
- **LLM/retriever/embeddings smoke tests**: `tests/test-your-llm.py`, `tests/test-your-retriever.py`, `tests/test-your-embeddings.py`
- **Security**: `tests/test_security_fix.py`
- **MCP**: `tests/test_mcp.py`
- **Logging**: `tests/test_logging.py`, `tests/test_logs.py`, `tests/test_logging_output.py`
- **Document loaders**: `tests/test-loaders.py`, `tests/documents-report-source.py`

### Important Testing Notes
- Most integration tests require real API keys (`OPENAI_API_KEY`, `TAVILY_API_KEY`).
- The CI Docker test workflow (`.github/workflows/docker-build.yml`) runs `tests/report-types.py` and `tests/vector-store.py` inside a container.
- Many tests mock the WebSocket with `AsyncMock` and use `CustomLogsHandler` from `backend.server.server_utils`.

---

## Code Style Guidelines

### Python
- **Python 3.11+** syntax is expected. Use modern type hints (`list[str] | None`, `str | None`, etc.).
- Write **docstrings** for modules, classes, and public methods.
- Use **type hints** on function signatures.
- Keep configuration in `gpt_researcher/config/variables/default.py` and load through the `Config` class.
- Use the project enums in `gpt_researcher.utils.enum` for report types, sources, tones, and prompt families.
- Prefer `pathlib.Path` over raw string paths for new code.
- Logging: use the standard `logging` module (configured in `main.py`). Some legacy code uses `loguru`.

### Frontend (Next.js / TypeScript)
- Next.js 14 App Router pattern (`app/` directory).
- Tailwind CSS for styling.
- Prettier + ESLint are configured in `frontend/nextjs/`.

### General
- Follow existing file organization: one directory per retriever/scraper under `gpt_researcher/retrievers/` and `gpt_researcher/scraper/`.
- When adding a new retriever or scraper, provide an `__init__.py` exposing a consistent interface matching existing ones.

---

## Configuration and Environment Variables

Key env vars (see `.env.example` for the full template):

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | LLM calls (required unless using another provider) | — |
| `TAVILY_API_KEY` | Web search (required unless using another retriever) | — |
| `OPENAI_BASE_URL` | Custom OpenAI-compatible endpoint | — |
| `RETRIEVER` | Comma-separated list of retrievers | `tavily` |
| `DOC_PATH` | Path to local documents for research | `./my-docs` |
| `FAST_LLM` / `SMART_LLM` / `STRATEGIC_LLM` | Model selectors | `openai:gpt-4o-mini`, `openai:gpt-4.1`, `openai:o4-mini` |
| `SCRAPER` | Default scraper backend | `bs` |
| `MAX_SCRAPER_WORKERS` | Concurrent scraper limit | `15` |
| `SCRAPER_RATE_LIMIT_DELAY` | Seconds between scraper requests | `0.0` |
| `LANGCHAIN_TRACING_V2` + `LANGCHAIN_API_KEY` | LangSmith observability | disabled |
| `GOOGLE_API_KEY` | Inline image generation (Gemini) | — |
| `IMAGE_GENERATION_ENABLED` | Enable AI-generated inline images | `false` |

Configuration hierarchy: environment variables > JSON config file > `DEFAULT_CONFIG` in `gpt_researcher/config/variables/default.py`.

---

## Deployment Process

1. **Build** (`.github/workflows/build.yml`):
   - Triggered on push to `master` (ignoring `terraform/**` changes).
   - Builds a Docker image with a timestamp+SHA tag.
   - Pushes to AWS ECR.
   - Triggers the Terraform deploy workflow.

2. **Deploy** (`.github/workflows/deploy.yml`):
   - Terraform plan/apply for AWS infrastructure.
   - Uses the image tag from the build workflow.

3. **Docker Compose** (local/staging):
   - `gpt-researcher` service on port `8000`
   - `gptr-nextjs` service on port `3000`
   - Optional `discord-bot` and `gpt-researcher-tests` profiles.

---

## Security Considerations

- **API keys** must be passed via environment variables or `.env`. Never commit them.
- **File uploads** are handled in `backend/server/server_utils.py` with filename sanitization (`sanitize_filename`).
- **CORS** is enabled in FastAPI for frontend communication.
- **MCP servers** respect `MCP_ALLOWED_ROOT_PATHS` to restrict local file access.
- The Dockerfile creates a **non-root user** (`gpt-researcher`) for the final stage.
- Output directories (`outputs/`, `logs/`, `my-docs/`) are created at runtime with appropriate permissions.

---

## Common Patterns for Agents

### Adding a New Retriever
1. Create a directory under `gpt_researcher/retrievers/<name>/`.
2. Implement a class with a `search(query)` async method returning a list of dicts with `title`, `href`, `body`.
3. Register it in `gpt_researcher/actions/retriever.py`.

### Adding a New Scraper
1. Create a directory under `gpt_researcher/scraper/<name>/`.
2. Implement the scrape interface consistent with existing scrapers.
3. Register in `gpt_researcher/scraper/scraper.py`.

### Adding a New Report Type
1. Add the enum value to `gpt_researcher/utils/enum.py` (`ReportType`).
2. Update prompts in `gpt_researcher/prompts.py` if needed.
3. Add orchestration logic in `backend/report_type/` or `gpt_researcher/skills/writer.py`.

### Running Research Programmatically
```python
from gpt_researcher import GPTResearcher

researcher = GPTResearcher(query="...", report_type="research_report")
await researcher.conduct_research()
report = await researcher.write_report()
```

---

## Useful References

- **Main agent class**: `gpt_researcher/agent.py`
- **FastAPI app**: `backend/server/app.py`
- **Config defaults**: `gpt_researcher/config/variables/default.py`
- **CLI**: `cli.py`
- **Tests**: `tests/`
- **Documentation site**: `docs/` (Docusaurus)
- **Docker entrypoint**: `main.py` runs `uvicorn main:app`
