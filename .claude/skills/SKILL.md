---
name: gpt-researcher
description: GPT Researcher is an autonomous deep research agent that conducts web and local research, producing detailed reports with citations. Use this skill when helping developers understand, extend, debug, or integrate with GPT Researcher - including adding features, understanding the architecture, working with the API, or customizing research workflows.
---

# GPT Researcher Development Skill

GPT Researcher is an LLM-based autonomous agent that conducts comprehensive research and generates detailed, factual reports with citations. It uses a planner-executor-publisher pattern with parallelized agent work for speed and reliability.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Core Components & Method Signatures](#core-components--method-signatures)
4. [End-to-End Research Flow](#end-to-end-research-flow)
5. [Data Flow Between Components](#data-flow-between-components)
6. [The Prompt System](#the-prompt-system)
7. [Retriever System](#retriever-system)
8. [MCP Integration](#mcp-integration)
9. [Deep Research Mode](#deep-research-mode)
10. [Multi-Agent System](#multi-agent-system)
11. [Image Generation (Real Case Study)](#image-generation-real-case-study)
12. [Adding New Features - The 8-Step Pattern](#adding-new-features---the-8-step-pattern)
13. [Advanced Usage Patterns](#advanced-usage-patterns)
14. [Error Handling Patterns](#error-handling-patterns)
15. [Testing Guide](#testing-guide)
16. [Critical Gotchas](#critical-gotchas)

---

## Quick Start

### Basic Python Usage
```python
from gpt_researcher import GPTResearcher
import asyncio

async def main():
    researcher = GPTResearcher(
        query="What are the latest AI developments?",
        report_type="research_report",
        report_source="web",
    )
    await researcher.conduct_research()
    report = await researcher.write_report()
    print(report)

asyncio.run(main())
```

### With WebSocket Streaming
```python
class WebSocketHandler:
    async def send_json(self, data):
        print(f"[{data['type']}] {data.get('output', data.get('content', ''))}")

researcher = GPTResearcher(
    query="AI developments",
    websocket=WebSocketHandler(),
)
```

### With MCP Data Sources
```python
researcher = GPTResearcher(
    query="Open source AI projects",
    mcp_configs=[{
        "name": "github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
    }],
    mcp_strategy="deep",  # or "fast", "disabled"
)
```

### With Local Documents
```python
researcher = GPTResearcher(
    query="Summarize my documents",
    report_source="local",  # Uses DOC_PATH env var
)
# Or hybrid (local + web)
researcher = GPTResearcher(
    query="Compare with industry trends",
    report_source="hybrid",
)
```

### Run Servers
```bash
# Backend
python -m uvicorn backend.server.server:app --reload --port 8000

# Frontend
cd frontend/nextjs && npm install && npm run dev
```

---

## Architecture Deep Dive

### System Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
│              (query, report_type, report_source, tone, mcp_configs)         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND API LAYER                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  FastAPI Server  │  │ WebSocket Manager│  │  Report Store    │          │
│  │  backend/server/ │  │ Real-time events │  │  JSON persistence│          │
│  │  app.py          │  │ websocket_mgr.py │  │  report_store.py │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GPTResearcher (gpt_researcher/agent.py)                   │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         SKILLS LAYER                                   │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐         │  │
│  │  │ ResearchConductor│ │ ReportGenerator │ │ ContextManager  │         │  │
│  │  │ Plan & gather   │ │ Write reports   │ │ Similarity search│         │  │
│  │  │ researcher.py   │ │ writer.py       │ │ context_manager │         │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘         │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐         │  │
│  │  │ BrowserManager  │ │ SourceCurator   │ │ ImageGenerator  │         │  │
│  │  │ Web scraping    │ │ Rank sources    │ │ Gemini images   │         │  │
│  │  │ browser.py      │ │ curator.py      │ │ image_generator │         │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘         │  │
│  │  ┌─────────────────┐                                                  │  │
│  │  │ DeepResearchSkill│                                                 │  │
│  │  │ Recursive depth │                                                  │  │
│  │  │ deep_research.py│                                                  │  │
│  │  └─────────────────┘                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        ACTIONS LAYER                                   │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐         │  │
│  │  │ report_generation│ │ query_processing│ │ web_scraping    │         │  │
│  │  │ LLM report write│ │ Sub-query plan  │ │ URL scraping    │         │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘         │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐         │  │
│  │  │ retriever.py    │ │ agent_creator   │ │ markdown_process│         │  │
│  │  │ Get retrievers  │ │ Choose agent    │ │ Parse markdown  │         │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       PROVIDERS LAYER                                  │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐         │  │
│  │  │ LLM Provider    │ │ Retrievers      │ │ Scrapers        │         │  │
│  │  │ OpenAI,Anthropic│ │ Tavily,Google   │ │ BS4,Playwright  │         │  │
│  │  │ Google,Groq...  │ │ Bing,MCP...     │ │ PDF,DOCX...     │         │  │
│  │  │ llm_provider/   │ │ retrievers/     │ │ scraper/        │         │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘         │  │
│  │  ┌─────────────────┐                                                  │  │
│  │  │ ImageGenerator  │                                                  │  │
│  │  │ Gemini/Imagen   │                                                  │  │
│  │  │ llm_provider/   │                                                  │  │
│  │  │ image/          │                                                  │  │
│  │  └─────────────────┘                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONFIGURATION LAYER                                   │
│                     gpt_researcher/config/                                   │
│                                                                              │
│     Environment Variables  →  JSON Config File  →  Default Values            │
│           (highest)              (medium)            (lowest)                │
│                                                                              │
│     config.py loads and merges all sources                                   │
│     variables/default.py contains all defaults                               │
│     variables/base.py defines TypedDict for type safety                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key File Locations

| Need | Primary File | Key Classes/Functions |
|------|--------------|----------------------|
| Main orchestrator | `gpt_researcher/agent.py` | `GPTResearcher` |
| Research logic | `gpt_researcher/skills/researcher.py` | `ResearchConductor` |
| Report writing | `gpt_researcher/skills/writer.py` | `ReportGenerator` |
| Context/embeddings | `gpt_researcher/skills/context_manager.py` | `ContextManager` |
| Source ranking | `gpt_researcher/skills/curator.py` | `SourceCurator` |
| Deep research | `gpt_researcher/skills/deep_research.py` | `DeepResearchSkill` |
| Image generation | `gpt_researcher/skills/image_generator.py` | `ImageGenerator` |
| All prompts | `gpt_researcher/prompts.py` | `PromptFamily` |
| Configuration | `gpt_researcher/config/config.py` | `Config` |
| Config defaults | `gpt_researcher/config/variables/default.py` | `DEFAULT_CONFIG` |
| Config types | `gpt_researcher/config/variables/base.py` | `BaseConfig` |
| API server | `backend/server/app.py` | FastAPI `app` |
| WebSocket mgmt | `backend/server/websocket_manager.py` | `WebSocketManager`, `run_agent` |
| Report types | `backend/report_type/` | `BasicReport`, `DetailedReport` |
| Search engines | `gpt_researcher/retrievers/` | `TavilySearch`, `GoogleSearch`, etc. |
| Web scraping | `gpt_researcher/scraper/` | Various scrapers |
| Enums | `gpt_researcher/utils/enum.py` | `ReportType`, `ReportSource`, `Tone` |

---

## Core Components & Method Signatures

### GPTResearcher (`gpt_researcher/agent.py`)

The main orchestrator class. Full initialization signature:

```python
class GPTResearcher:
    def __init__(
        self,
        query: str,                              # Research question (required)
        report_type: str = "research_report",    # research_report, detailed_report, deep, outline_report, resource_report
        report_format: str = "markdown",         # Output format
        report_source: str = "web",              # web, local, hybrid, azure, langchain_documents, langchain_vectorstore
        tone: Tone = Tone.Objective,             # Writing tone (see Tone enum)
        source_urls: list[str] | None = None,    # Specific URLs to research
        document_urls: list[str] | None = None,  # Document URLs to include
        complement_source_urls: bool = False,    # Add web search to source_urls
        query_domains: list[str] | None = None,  # Restrict search to domains
        documents=None,                          # LangChain document objects
        vector_store=None,                       # LangChain vector store
        vector_store_filter=None,                # Filter for vector store
        config_path=None,                        # Path to JSON config file
        websocket=None,                          # WebSocket for streaming
        agent=None,                              # Pre-defined agent type
        role=None,                               # Pre-defined agent role
        parent_query: str = "",                  # Parent query for subtopics
        subtopics: list | None = None,           # Subtopics to research
        visited_urls: set | None = None,         # Already visited URLs
        verbose: bool = True,                    # Verbose logging
        context=None,                            # Pre-loaded context
        headers: dict | None = None,             # HTTP headers
        max_subtopics: int = 5,                  # Max subtopics for detailed
        log_handler=None,                        # Custom log handler
        prompt_family: str | None = None,        # Custom prompt family
        mcp_configs: list[dict] | None = None,   # MCP server configurations
        mcp_max_iterations: int | None = None,   # Deprecated, use mcp_strategy
        mcp_strategy: str | None = None,         # fast, deep, disabled
        **kwargs
    ):
```

**Key Methods:**

```python
async def conduct_research(self, on_progress=None) -> str:
    """
    Main research orchestration.
    
    1. Selects agent role via LLM (choose_agent)
    2. Delegates to ResearchConductor
    3. Optionally generates images if enabled
    
    Returns: Accumulated research context as string
    """

async def write_report(
    self, 
    existing_headers: list = [],           # Headers to avoid duplication
    relevant_written_contents: list = [],  # Previous content for context
    ext_context=None,                      # External context override
    custom_prompt=""                       # Custom prompt override
) -> str:
    """
    Generate final report from context.
    
    Returns: Markdown report string
    """

def get_costs(self) -> float:
    """Returns total accumulated API costs."""

def add_costs(self, cost: float) -> None:
    """Add to running cost total (used as callback)."""
```

### ResearchConductor (`gpt_researcher/skills/researcher.py`)

Manages the research process:

```python
class ResearchConductor:
    def __init__(self, researcher: GPTResearcher):
        self.researcher = researcher
        self.logger = logging.getLogger(__name__)

    async def plan_research(self, query: str, query_domains=None) -> list:
        """
        Generate sub-queries from main query using LLM.
        
        1. Gets initial search results
        2. Calls plan_research_outline() to generate sub-queries
        
        Returns: List of sub-query strings
        """

    async def conduct_research(self) -> str:
        """
        Main research execution based on report_source.
        
        Handles: web, local, hybrid, azure, langchain_documents, langchain_vectorstore
        
        For each source type:
        1. Load/search data
        2. Process sub-queries
        3. Combine context
        4. Optionally curate sources
        
        Returns: Combined research context string
        """

    async def _process_sub_query(
        self, 
        sub_query: str, 
        scraped_data: list = [], 
        query_domains: list = []
    ) -> str:
        """
        Process a single sub-query.
        
        1. Get MCP context (if configured, based on strategy)
        2. Scrape URLs from search results
        3. Get similar content via embeddings
        4. Combine MCP + web context
        
        Returns: Combined context for this sub-query
        """

    async def _get_context_by_web_search(
        self, 
        query: str, 
        scraped_data: list = [], 
        query_domains: list = []
    ) -> str:
        """Web-based research with sub-query planning."""

    async def _scrape_data_by_urls(
        self, 
        sub_query: str, 
        query_domains: list = []
    ) -> list:
        """Search and scrape URLs for a sub-query."""
```

### ReportGenerator (`gpt_researcher/skills/writer.py`)

```python
class ReportGenerator:
    def __init__(self, researcher: GPTResearcher):
        self.researcher = researcher
        self.research_params = {
            "query": researcher.query,
            "agent_role_prompt": researcher.cfg.agent_role or researcher.role,
            "report_type": researcher.report_type,
            "report_source": researcher.report_source,
            "tone": researcher.tone,
            "websocket": researcher.websocket,
            "cfg": researcher.cfg,
            "headers": researcher.headers,
        }

    async def write_report(
        self,
        existing_headers: list = [],
        relevant_written_contents: list = [],
        ext_context=None,
        custom_prompt="",
        available_images: list = [],  # Pre-generated images to embed
    ) -> str:
        """
        Generate report using LLM.
        
        Calls generate_report() action with context and images.
        
        Returns: Markdown report
        """

    async def write_introduction(self, ...) -> str:
        """Write report introduction section."""

    async def write_conclusion(self, ...) -> str:
        """Write report conclusion with references."""
```

---

## End-to-End Research Flow

### 1. Request Entry (`backend/server/app.py`)

```python
# REST API endpoint
@app.post("/report/")
async def generate_report(research_request: ResearchRequest, background_tasks: BackgroundTasks):
    research_id = sanitize_filename(f"task_{int(time.time())}_{research_request.task}")
    # Calls write_report() which uses run_agent()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await handle_websocket_communication(websocket, manager)
```

### 2. Agent Runner (`backend/server/websocket_manager.py`)

```python
async def run_agent(task, report_type, report_source, source_urls, ...):
    """
    Main entry point for research execution.
    """
    # Create logs handler
    logs_handler = CustomLogsHandler(websocket, task)
    
    # Configure MCP if enabled
    if mcp_enabled and mcp_configs:
        os.environ["RETRIEVER"] = f"{current_retriever},mcp"
        os.environ["MCP_STRATEGY"] = mcp_strategy
    
    # Route based on report type
    if report_type == "multi_agents":
        report = await run_research_task(query=task, websocket=logs_handler, ...)
    elif report_type == ReportType.DetailedReport.value:
        researcher = DetailedReport(query=task, ...)
        report = await researcher.run()
    else:
        researcher = BasicReport(query=task, ...)
        report = await researcher.run()
    
    return report
```

### 3. Research Phase (`gpt_researcher/agent.py`)

```python
async def conduct_research(self, on_progress=None):
    # Handle deep research separately
    if self.report_type == ReportType.DeepResearch.value and self.deep_researcher:
        return await self._handle_deep_research(on_progress)
    
    # Choose agent role via LLM
    if not (self.agent and self.role):
        self.agent, self.role = await choose_agent(
            query=self.query,
            cfg=self.cfg,
            parent_query=self.parent_query,
            cost_callback=self.add_costs,
            headers=self.headers,
            prompt_family=self.prompt_family,
        )
    
    # Conduct research
    self.context = await self.research_conductor.conduct_research()
    
    # Generate images if enabled (pre-generation for seamless UX)
    if self.cfg.image_generation_enabled and self.image_generator:
        self.available_images = await self.image_generator.plan_and_generate_images(
            research_context=self.context,
            research_query=self.query,
            research_id=self.research_id,
            websocket=self.websocket,
        )
    
    return self.context
```

### 4. Sub-Query Processing (`gpt_researcher/skills/researcher.py`)

```python
async def _process_sub_query(self, sub_query: str, scraped_data: list = [], query_domains: list = []):
    # MCP Strategy handling
    mcp_retrievers = [r for r in self.researcher.retrievers if "mcpretriever" in r.__name__.lower()]
    mcp_strategy = self._get_mcp_strategy()
    
    if mcp_retrievers:
        if mcp_strategy == "fast" and self._mcp_results_cache is not None:
            # Reuse cached MCP results
            mcp_context = self._mcp_results_cache.copy()
        elif mcp_strategy == "deep":
            # Run MCP for every sub-query
            mcp_context = await self._execute_mcp_research_for_queries([sub_query], mcp_retrievers)
    
    # Get web search context
    if not scraped_data:
        scraped_data = await self._scrape_data_by_urls(sub_query, query_domains)
    
    # Get similar content via embeddings
    if scraped_data:
        web_context = await self.researcher.context_manager.get_similar_content_by_query(
            sub_query, scraped_data
        )
    
    # Combine MCP + web context
    combined_context = self._combine_mcp_and_web_context(mcp_context, web_context, sub_query)
    return combined_context
```

### 5. Report Generation (`gpt_researcher/actions/report_generation.py`)

```python
async def generate_report(
    query: str,
    context: str,
    agent_role_prompt: str,
    report_type: str,
    websocket=None,
    cfg=None,
    tone=None,
    headers=None,
    cost_callback=None,
    prompt_family=None,
    available_images: list = [],
    **kwargs
) -> str:
    """
    Generate report using LLM.
    """
    # Get prompt generator
    generate_prompt = prompt_family.get_prompt_by_report_type(report_type)
    
    # Build prompt with context and available images
    content = generate_prompt(
        query, context, report_source,
        report_format=cfg.report_format,
        tone=tone,
        total_words=cfg.total_words,
        language=cfg.language,
        available_images=available_images,
    )
    
    # Call LLM
    report = await create_chat_completion(
        model=cfg.smart_llm,
        messages=[{"role": "user", "content": content}],
        temperature=cfg.temperature,
        llm_provider=cfg.smart_llm_provider,
        max_tokens=cfg.smart_token_limit,
        llm_kwargs=cfg.llm_kwargs,
        cost_callback=cost_callback,
    )
    
    return report
```

---

## Data Flow Between Components

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ GPTResearcher.__init__()                                         │
│   • Loads Config (env → json → defaults)                        │
│   • Initializes skills: ResearchConductor, ReportGenerator, etc │
│   • Initializes retrievers based on RETRIEVER env var           │
│   • Initializes ImageGenerator if IMAGE_GENERATION_ENABLED      │
└─────────────────────────────────────────────────────────────────┘
    │
    │  researcher.conduct_research()
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ choose_agent()                                                   │
│   Input: query, config                                          │
│   Output: (agent_type: str, role_prompt: str)                   │
│   • LLM selects best agent role for the query                   │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ResearchConductor.conduct_research()                             │
│   Input: self.researcher (has query, config, retrievers)        │
│   Output: context: str                                          │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ plan_research()                                          │   │
│   │   Input: query                                           │   │
│   │   Output: sub_queries: list[str]                         │   │
│   │   • Calls LLM to generate 3-5 sub-queries                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ For each sub_query:                                      │   │
│   │   _process_sub_query()                                   │   │
│   │     Input: sub_query                                     │   │
│   │     Output: sub_context: str                             │   │
│   │                                                          │   │
│   │     1. MCP retrieval (if configured)                     │   │
│   │        → mcp_context: list[dict]                         │   │
│   │                                                          │   │
│   │     2. Web search via retrievers                         │   │
│   │        → search_results: list[dict]                      │   │
│   │                                                          │   │
│   │     3. Scrape URLs                                       │   │
│   │        → scraped_content: list[dict]                     │   │
│   │                                                          │   │
│   │     4. Similarity search via embeddings                  │   │
│   │        → relevant_context: str                           │   │
│   │                                                          │   │
│   │     5. Combine MCP + web context                         │   │
│   │        → combined_context: str                           │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│   Aggregate all sub_contexts → final context: str               │
└─────────────────────────────────────────────────────────────────┘
    │
    │  If IMAGE_GENERATION_ENABLED:
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ImageGenerator.plan_and_generate_images()                        │
│   Input: context, query, research_id                            │
│   Output: available_images: list[dict]                          │
│     [{"url": "/outputs/images/.../img.png",                     │
│       "title": "...", "description": "..."}]                    │
│                                                                  │
│   1. LLM analyzes context for visual concepts                   │
│   2. Generates 2-3 images in parallel via Gemini                │
│   3. Saves to outputs/images/{research_id}/                     │
└─────────────────────────────────────────────────────────────────┘
    │
    │  researcher.write_report()
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ReportGenerator.write_report()                                   │
│   Input: context, available_images                              │
│   Output: report: str (markdown)                                │
│                                                                  │
│   → generate_report() action                                    │
│       • Builds prompt with context + image list                 │
│       • LLM generates report with embedded images               │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Output                                                           │
│   • Streamed via WebSocket (type: "report")                     │
│   • Final via WebSocket (type: "report_complete")               │
│   • Exported to PDF, DOCX, Markdown                             │
│   • Saved to outputs/ directory                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Prompt System

### PromptFamily Class (`gpt_researcher/prompts.py`)

All prompts are centralized in the `PromptFamily` class. This allows for model-specific prompt variations.

```python
class PromptFamily:
    """
    General purpose class for prompt formatting.
    Can be overwritten with model-specific derived classes.
    """

    def __init__(self, config: Config):
        self.cfg = config

    @staticmethod
    def get_prompt_by_report_type(report_type: str):
        """Returns the appropriate prompt generator for the report type."""
        match report_type:
            case ReportType.ResearchReport.value:
                return PromptFamily.generate_report_prompt
            case ReportType.DetailedReport.value:
                return PromptFamily.generate_report_prompt
            case ReportType.OutlineReport.value:
                return PromptFamily.generate_outline_report_prompt
            # ... etc
```

### Key Prompt Examples

**Agent Selection Prompt:**
```python
@staticmethod
def generate_agent_role_prompt(query: str, parent_query: str = "") -> str:
    return f"""Analyze the research query and select the most appropriate agent role.

Query: "{query}"
{f'Parent Query: "{parent_query}"' if parent_query else ''}

Based on the query, determine:
1. The domain expertise needed
2. The research approach required
3. The appropriate agent persona

Return a JSON object with:
- "agent": The agent type (e.g., "Research Analyst", "Technical Writer")
- "role": A detailed role description for how the agent should approach this research
"""
```

**Research Planning Prompt:**
```python
@staticmethod
def generate_search_queries_prompt(
    query: str,
    parent_query: str = "",
    report_type: str = "",
    max_iterations: int = 3,
    context: str = "",
) -> str:
    return f"""Generate {max_iterations} focused search queries to research: "{query}"

Context from initial search:
{context}

Requirements:
- Each query should explore a different aspect
- Queries should be specific and searchable
- Consider the report type: {report_type}

Return a JSON array of query strings.
"""
```

**Report Generation Prompt (with images):**
```python
@staticmethod
def generate_report_prompt(
    question: str,
    context: str,
    report_source: str,
    report_format="apa",
    total_words=1000,
    tone=None,
    language="english",
    available_images: list = [],
) -> str:
    # Build image embedding instruction if images available
    image_instruction = ""
    if available_images:
        image_list = "\n".join([
            f"- Title: {img.get('title')}\n  URL: {img['url']}"
            for img in available_images
        ])
        image_instruction = f"""
AVAILABLE IMAGES (embed where relevant):
{image_list}

Use markdown format: ![Title](URL)
"""

    return f"""Information: "{context}"
---
Using the above information, answer: "{question}" in a detailed report.

- Format: {report_format}
- Length: ~{total_words} words
- Tone: {tone.value if tone else "Objective"}
- Language: {language}
- Include citations for all factual claims
{image_instruction}
"""
```

**MCP Tool Selection Prompt:**
```python
@staticmethod
def generate_mcp_tool_selection_prompt(query: str, tools_info: list, max_tools: int = 3) -> str:
    return f"""Select the most relevant tools for researching: "{query}"

AVAILABLE TOOLS:
{json.dumps(tools_info, indent=2)}

Select exactly {max_tools} tools ranked by relevance.

Return JSON:
{{
  "selected_tools": [
    {{"index": 0, "name": "tool_name", "relevance_score": 9, "reason": "..."}}
  ]
}}
"""
```

---

## Retriever System

### Available Retrievers (`gpt_researcher/retrievers/`)

| Retriever | Class | API Key Env Var |
|-----------|-------|-----------------|
| Tavily | `TavilySearch` | `TAVILY_API_KEY` |
| Google | `GoogleSearch` | `GOOGLE_API_KEY`, `GOOGLE_CX_KEY` |
| DuckDuckGo | `Duckduckgo` | None |
| Bing | `BingSearch` | `BING_API_KEY` |
| Serper | `SerperSearch` | `SERPER_API_KEY` |
| SerpAPI | `SerpApiSearch` | `SERPAPI_API_KEY` |
| SearchAPI | `SearchApiSearch` | `SEARCHAPI_API_KEY` |
| Exa | `ExaSearch` | `EXA_API_KEY` |
| arXiv | `ArxivSearch` | None |
| Semantic Scholar | `SemanticScholarSearch` | None |
| PubMed Central | `PubMedCentralSearch` | None |
| MCP | `MCPRetriever` | Per-server |
| Custom | `CustomRetriever` | User-defined |

### Retriever Selection (`gpt_researcher/actions/retriever.py`)

```python
def get_retriever(retriever: str):
    """Get a retriever class by name."""
    match retriever:
        case "tavily":
            from gpt_researcher.retrievers import TavilySearch
            return TavilySearch
        case "google":
            from gpt_researcher.retrievers import GoogleSearch
            return GoogleSearch
        case "mcp":
            from gpt_researcher.retrievers import MCPRetriever
            return MCPRetriever
        # ... etc

def get_retrievers(retriever_names: str, headers: dict = None) -> list:
    """
    Get multiple retrievers from comma-separated string.
    
    Usage: RETRIEVER=tavily,google,mcp
    """
    retrievers = []
    for name in retriever_names.split(","):
        retriever_class = get_retriever(name.strip())
        if retriever_class:
            retrievers.append(retriever_class)
    return retrievers
```

### Adding a New Retriever

1. Create file: `gpt_researcher/retrievers/my_retriever/my_retriever.py`
```python
class MyRetriever:
    def __init__(self, query: str, headers: dict = None):
        self.query = query
        self.headers = headers
    
    async def search(self, max_results: int = 10) -> list[dict]:
        """
        Returns list of:
        {
            "title": str,
            "href": str,
            "body": str
        }
        """
        # Implementation
        pass
```

2. Register in `gpt_researcher/actions/retriever.py`:
```python
case "my_retriever":
    from gpt_researcher.retrievers.my_retriever import MyRetriever
    return MyRetriever
```

3. Export in `gpt_researcher/retrievers/__init__.py`:
```python
from .my_retriever import MyRetriever
__all__ = [..., "MyRetriever"]
```

---

## MCP Integration

### MCP (Model Context Protocol) Overview

MCP enables research from specialized data sources (GitHub, databases, APIs) alongside web search.

### MCP Configuration

```python
researcher = GPTResearcher(
    query="...",
    mcp_configs=[
        {
            "name": "github",                    # Server name
            "command": "npx",                    # Command to start
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": "..."},      # Environment vars
        },
        {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem", "/docs"],
        },
        {
            "name": "remote",
            "connection_url": "ws://server:8080",  # WebSocket connection
            "connection_type": "websocket",
            "connection_token": "auth_token",
        }
    ],
    mcp_strategy="fast",  # fast, deep, disabled
)
```

### MCP Strategy Options

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `fast` (default) | Run MCP once with original query, cache results | Performance-focused |
| `deep` | Run MCP for every sub-query | Maximum thoroughness |
| `disabled` | Skip MCP entirely | Web-only research |

### MCP Processing Logic (`gpt_researcher/skills/researcher.py`)

```python
# At start of research (for 'fast' strategy)
if mcp_strategy == "fast":
    mcp_context = await self._execute_mcp_research_for_queries([query], mcp_retrievers)
    self._mcp_results_cache = mcp_context  # Cache for reuse

# During sub-query processing
if mcp_strategy == "fast" and self._mcp_results_cache is not None:
    mcp_context = self._mcp_results_cache.copy()  # Reuse cache
elif mcp_strategy == "deep":
    mcp_context = await self._execute_mcp_research_for_queries([sub_query], mcp_retrievers)
```

---

## Deep Research Mode

### Overview

Deep Research uses recursive tree-like exploration with configurable depth and breadth.

### Configuration

```bash
DEEP_RESEARCH_BREADTH=4    # Subtopics per level
DEEP_RESEARCH_DEPTH=2      # Recursion levels
DEEP_RESEARCH_CONCURRENCY=2  # Parallel tasks
```

### DeepResearchSkill (`gpt_researcher/skills/deep_research.py`)

```python
class DeepResearchSkill:
    def __init__(self, researcher):
        self.researcher = researcher
        self.breadth = getattr(researcher.cfg, 'deep_research_breadth', 4)
        self.depth = getattr(researcher.cfg, 'deep_research_depth', 2)
        self.concurrency_limit = getattr(researcher.cfg, 'deep_research_concurrency', 2)
        self.learnings = []
        self.research_sources = []
        self.context = []

    async def deep_research(self, query: str, on_progress=None) -> str:
        """
        Recursive research with depth and breadth.
        
        1. Research main topic
        2. Generate subtopics (breadth)
        3. For each subtopic, recursively research (depth)
        4. Aggregate all findings
        5. Generate comprehensive report
        """
```

### Usage

```python
researcher = GPTResearcher(
    query="Comprehensive analysis of quantum computing",
    report_type="deep",  # Triggers deep research
)
await researcher.conduct_research()
report = await researcher.write_report()
```

---

## Multi-Agent System

### Overview (`multi_agents/`)

LangGraph-based system inspired by [STORM paper](https://arxiv.org/abs/2402.14207). Generates 5-6 page reports with multiple agents collaborating.

### Agent Roles

| Agent | File | Role |
|-------|------|------|
| Human | - | Oversees and provides feedback |
| Chief Editor | `agents/editor.py` | Master coordinator via LangGraph |
| Researcher | Uses GPTResearcher | Deep research on topics |
| Editor | `agents/editor.py` | Plans outline and structure |
| Reviewer | `agents/reviewer.py` | Validates research correctness |
| Revisor | `agents/revisor.py` | Revises based on feedback |
| Writer | `agents/writer.py` | Compiles final report |
| Publisher | `agents/publisher.py` | Exports to PDF, DOCX, Markdown |

### Workflow

```
1. Browser (GPTResearcher) → Initial research
2. Editor → Plans report outline
3. For each outline topic (parallel):
   a. Researcher → In-depth subtopic research
   b. Reviewer → Validates draft
   c. Revisor → Revises until satisfactory
4. Writer → Compiles final report
5. Publisher → Exports to multiple formats
```

### Usage

```python
# Via API
report_type = "multi_agents"

# Or directly
from multi_agents import run_research_task

report = await run_research_task(
    query="...",
    websocket=handler,
    tone=Tone.Analytical,
)
```

---

## Image Generation (Real Case Study)

This section shows the **actual implementation** of the Image Generation feature as a reference for adding new features.

### 1. Configuration Added

**`gpt_researcher/config/variables/default.py`:**
```python
DEFAULT_CONFIG: BaseConfig = {
    # ... existing ...
    "IMAGE_GENERATION_MODEL": "models/gemini-2.5-flash-image",
    "IMAGE_GENERATION_MAX_IMAGES": 3,
    "IMAGE_GENERATION_ENABLED": False,
    "IMAGE_GENERATION_STYLE": "dark",  # dark, light, auto
}
```

### 2. Provider Created

**`gpt_researcher/llm_provider/image/image_generator.py`:**
```python
class ImageGeneratorProvider:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model or "models/gemini-2.5-flash-image"
        self._client = None
    
    def is_enabled(self) -> bool:
        return bool(self.api_key and self.model)
    
    def _build_enhanced_prompt(self, prompt: str, context: str = "", style: str = "dark") -> str:
        """Add styling instructions to prompt."""
        if style == "dark":
            style_instructions = """
            Style: Dark mode professional infographic
            - Background: Dark (#0d1117)
            - Accents: Teal/cyan (#14b8a6)
            - Clean, modern, minimalist
            """
        # ... handle light, auto
        return f"{style_instructions}\n\nCreate: {prompt}\n\nContext: {context}"
    
    async def generate_image(
        self,
        prompt: str,
        context: str = "",
        research_id: str = "",
        style: str = "dark",
    ) -> List[Dict[str, Any]]:
        """Generate image using Gemini."""
        full_prompt = self._build_enhanced_prompt(prompt, context, style)
        
        # Call Gemini API
        response = await self._generate_with_gemini(full_prompt, output_path, ...)
        
        return [{"url": f"/outputs/images/{research_id}/img_{hash}.png", ...}]
```

### 3. Skill Created

**`gpt_researcher/skills/image_generator.py`:**
```python
class ImageGenerator:
    def __init__(self, researcher):
        self.researcher = researcher
        self.config = researcher.cfg
        self.image_provider = ImageGeneratorProvider(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=getattr(self.config, 'image_generation_model', None),
        )
        self.max_images = getattr(self.config, 'image_generation_max_images', 3)
        self.style = getattr(self.config, 'image_generation_style', 'dark')
    
    def is_enabled(self) -> bool:
        enabled = getattr(self.config, 'image_generation_enabled', False)
        return enabled and self.image_provider.is_enabled()
    
    async def plan_and_generate_images(
        self,
        research_context: str,
        research_query: str,
        research_id: str,
        websocket: Any,
    ) -> List[Dict[str, Any]]:
        """
        1. Use LLM to identify visual concepts from context
        2. Generate images in parallel
        3. Return list of image metadata
        """
        # Stream progress
        await stream_output("logs", "image_planning", "🎨 Planning images...", websocket)
        
        # LLM identifies concepts
        concepts = await self._plan_image_concepts(research_context, research_query)
        
        # Generate images in parallel
        generated_images = []
        for i, concept in enumerate(concepts[:self.max_images]):
            await stream_output("logs", "image_generating", 
                f"🖼️ Generating image {i+1}/{len(concepts)}...", websocket)
            
            images = await self.image_provider.generate_image(
                prompt=concept["prompt"],
                context=concept.get("context", ""),
                research_id=research_id,
                style=self.style,
            )
            generated_images.extend(images)
        
        await stream_output("logs", "images_ready", 
            f"✅ Generated {len(generated_images)} images", websocket)
        
        return generated_images
    
    async def _plan_image_concepts(self, context: str, query: str) -> List[Dict]:
        """Use LLM to identify visualization opportunities."""
        prompt = f"""Based on research about "{query}":

{context[:3000]}

Identify 2-3 concepts that would benefit from visual illustration.

Return JSON array:
[{{"concept": "...", "prompt": "detailed image prompt", "placement_hint": "after section X"}}]
"""
        response = await create_chat_completion(model=self.config.smart_llm, ...)
        return json.loads(response)
```

### 4. Agent Integration

**`gpt_researcher/agent.py`:**
```python
class GPTResearcher:
    def __init__(self, ...):
        # ... existing init ...
        
        # Initialize image generator if enabled
        if self.cfg.image_generation_enabled:
            from gpt_researcher.skills import ImageGenerator
            self.image_generator = ImageGenerator(self)
        else:
            self.image_generator = None
        
        self.available_images: List[Dict[str, Any]] = []
        self.research_id = self._generate_research_id(query)
    
    async def conduct_research(self, on_progress=None):
        # ... existing research ...
        
        self.context = await self.research_conductor.conduct_research()
        
        # Pre-generate images after research, before report writing
        if self.cfg.image_generation_enabled and self.image_generator and self.image_generator.is_enabled():
            self.available_images = await self.image_generator.plan_and_generate_images(
                research_context=self.context,
                research_query=self.query,
                research_id=self.research_id,
                websocket=self.websocket,
            )
        
        return self.context
    
    async def write_report(self, ...):
        report = await self.report_generator.write_report(
            # ... existing params ...
            available_images=self.available_images,  # Pass to report writer
        )
        return report
```

### 5. Prompt Updated

**`gpt_researcher/prompts.py`:**
```python
@staticmethod
def generate_report_prompt(..., available_images: List[Dict[str, Any]] = []):
    image_instruction = ""
    if available_images:
        image_list = "\n".join([
            f"- Title: {img.get('title', 'Untitled')}\n  URL: {img['url']}"
            for img in available_images
        ])
        image_instruction = f"""
AVAILABLE IMAGES - Embed where relevant using ![Title](URL):
{image_list}
"""
    
    return f"""...(existing prompt)...
{image_instruction}
"""
```

---

## Adding New Features - The 8-Step Pattern

```
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│1.CONFIG│ →  │2.PROVIDER│ → │3.SKILL │ →  │4.AGENT │
└────────┘    └────────┘    └────────┘    └────────┘
     ↓             ↓             ↓             ↓
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│5.PROMPTS│ → │6.WEBSOCKET│→ │7.FRONTEND│→ │8.DOCS  │
└────────┘    └────────┘    └────────┘    └────────┘
```

### Step 1: Add Configuration

**`gpt_researcher/config/variables/default.py`:**
```python
DEFAULT_CONFIG: BaseConfig = {
    "MY_FEATURE_ENABLED": False,
    "MY_FEATURE_MODEL": "model-name",
    "MY_FEATURE_MAX_ITEMS": 3,
}
```

**`gpt_researcher/config/variables/base.py`:**
```python
class BaseConfig(TypedDict):
    "MY_FEATURE_ENABLED": bool
    "MY_FEATURE_MODEL": Union[str, None]
    "MY_FEATURE_MAX_ITEMS": int
```

### Step 2: Create Provider

**`gpt_researcher/llm_provider/my_feature/my_provider.py`:**
```python
class MyFeatureProvider:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("MY_API_KEY")
        self.model = model
    
    def is_enabled(self) -> bool:
        return bool(self.api_key and self.model)
    
    async def execute(self, input_data: str) -> Dict[str, Any]:
        # API implementation
        pass
```

Export in `gpt_researcher/llm_provider/__init__.py`.

### Step 3: Create Skill

**`gpt_researcher/skills/my_feature.py`:**
```python
class MyFeatureSkill:
    def __init__(self, researcher):
        self.researcher = researcher
        self.config = researcher.cfg
        self.provider = MyFeatureProvider(...)
    
    def is_enabled(self) -> bool:
        return getattr(self.config, 'my_feature_enabled', False) and self.provider.is_enabled()
    
    async def execute(self, context: str, query: str) -> List[Dict]:
        if not self.is_enabled():
            return []
        
        await stream_output("logs", "my_feature_start", "🚀 Starting...", self.researcher.websocket)
        results = await self.provider.execute(context)
        await stream_output("logs", "my_feature_complete", "✅ Done", self.researcher.websocket)
        
        return results
```

Export in `gpt_researcher/skills/__init__.py`.

### Step 4: Integrate into Agent

**`gpt_researcher/agent.py`:**
```python
def __init__(self, ...):
    if self.cfg.my_feature_enabled:
        from gpt_researcher.skills import MyFeatureSkill
        self.my_feature = MyFeatureSkill(self)
    else:
        self.my_feature = None
    self.my_feature_results = []

async def conduct_research(self, ...):
    # ... existing ...
    if self.my_feature and self.my_feature.is_enabled():
        self.my_feature_results = await self.my_feature.execute(self.context, self.query)
```

### Step 5: Update Prompts

**`gpt_researcher/prompts.py`:**
```python
@staticmethod
def generate_my_feature_prompt(context: str, query: str) -> str:
    return f"""..."""
```

### Step 6: WebSocket Events

Already handled via `stream_output()` in skill.

### Step 7: Frontend (if needed)

**`frontend/nextjs/hooks/useWebSocket.ts`:**
```typescript
if (data.content === 'my_feature_start') {
    setStatus('processing');
}
```

### Step 8: Documentation

Create `docs/docs/gpt-researcher/gptr/my_feature.md`.

---

## Advanced Usage Patterns

### Custom Callbacks

```python
def cost_callback(cost: float):
    print(f"API call cost: ${cost}")

researcher = GPTResearcher(query="...")
researcher.add_costs = cost_callback  # Override cost tracking
```

### Custom WebSocket Handler

```python
class CustomWebSocket:
    def __init__(self):
        self.messages = []
    
    async def send_json(self, data):
        self.messages.append(data)
        if data['type'] == 'logs':
            print(f"Progress: {data['output']}")

researcher = GPTResearcher(query="...", websocket=CustomWebSocket())
```

### Using with LangChain Documents

```python
from langchain.document_loaders import DirectoryLoader

loader = DirectoryLoader('./docs', glob="**/*.md")
documents = loader.load()

researcher = GPTResearcher(
    query="Summarize the documentation",
    report_source="langchain_documents",
    documents=documents,
)
```

### Using with Vector Store

```python
from langchain.vectorstores import Chroma

vectorstore = Chroma.from_documents(documents, embeddings)

researcher = GPTResearcher(
    query="Find relevant information",
    report_source="langchain_vectorstore",
    vector_store=vectorstore,
    vector_store_filter={"source": "docs"},
)
```

### Restricting Search Domains

```python
researcher = GPTResearcher(
    query="Company news",
    query_domains=["reuters.com", "bloomberg.com", "wsj.com"],
)
```

### Using Specific Source URLs

```python
researcher = GPTResearcher(
    query="Analyze these articles",
    source_urls=[
        "https://example.com/article1",
        "https://example.com/article2",
    ],
    complement_source_urls=True,  # Also do web search
)
```

---

## Error Handling Patterns

### Graceful Degradation

```python
# In skills, always check is_enabled()
async def execute(self, ...):
    if not self.is_enabled():
        logger.warning("Feature not enabled, skipping")
        return []  # Return empty, don't crash
    
    try:
        result = await self.provider.execute(...)
        return result
    except Exception as e:
        logger.error(f"Feature error: {e}")
        await stream_output("logs", "feature_error", f"⚠️ Error: {e}", self.websocket)
        return []  # Graceful degradation
```

### API Rate Limiting

```python
# Providers should handle rate limits
async def execute(self, ...):
    try:
        return await self._call_api(...)
    except RateLimitError as e:
        logger.warning(f"Rate limited, waiting...")
        await asyncio.sleep(60)
        return await self._call_api(...)  # Retry
```

### WebSocket None Check

```python
# Always check websocket before sending
if self.researcher.websocket:
    await stream_output("logs", "event", "message", self.researcher.websocket)
```

---

## Testing Guide

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test
python -m pytest tests/test_researcher.py -v

# With coverage
python -m pytest tests/ --cov=gpt_researcher
```

### Local Development Setup

```bash
# Install in editable mode
pip install -e .

# Verify import
python -c "from gpt_researcher import GPTResearcher; print('OK')"
```

### Testing a New Feature

```python
# tests/test_my_feature.py
import pytest
from gpt_researcher import GPTResearcher

@pytest.mark.asyncio
async def test_my_feature_disabled():
    """Test that feature is skipped when disabled."""
    researcher = GPTResearcher(query="test")
    # MY_FEATURE_ENABLED defaults to False
    assert researcher.my_feature is None

@pytest.mark.asyncio
async def test_my_feature_enabled(monkeypatch):
    """Test feature execution when enabled."""
    monkeypatch.setenv("MY_FEATURE_ENABLED", "true")
    monkeypatch.setenv("MY_API_KEY", "test-key")
    
    researcher = GPTResearcher(query="test")
    assert researcher.my_feature is not None
    assert researcher.my_feature.is_enabled()
```

---

## Critical Gotchas

| ❌ Mistake | ✅ Correct | Why |
|-----------|-----------|-----|
| `config.MY_VAR` | `config.my_var` | Config keys are lowercased |
| Editing pip-installed package | `pip install -e .` | Need local editable install |
| Forgetting async/await | All research methods are async | Will get coroutine object |
| Not checking `is_enabled()` | Always check first | Feature may not be configured |
| Hardcoding API keys | Use `os.getenv()` | Security and flexibility |
| Missing `__init__.py` exports | Add to `__all__` | Won't be importable |
| `websocket.send_json()` on None | Check `if websocket:` first | Will crash |
| Blocking the event loop | Use `asyncio` for I/O | Will freeze the app |
| Not handling empty results | Return `[]` or `""` | Don't return `None` |
| Forgetting to register retriever | Add to `retriever.py` match | Won't be recognized |

---

## External Links

- [Official Documentation](https://docs.gptr.dev/)
- [GitHub Repository](https://github.com/assafelovic/gpt-researcher)
- [LangChain Documentation](https://python.langchain.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

For configuration and API reference, see [REFERENCE.md](REFERENCE.md).
