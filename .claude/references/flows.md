# Research Flow & Data Flow

## Table of Contents
- [End-to-End Research Flow](#end-to-end-research-flow)
- [Data Flow Between Components](#data-flow-between-components)

---

## End-to-End Research Flow

### 1. Request Entry

**File:** `backend/server/app.py`

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

### 2. Agent Runner

**File:** `backend/server/websocket_manager.py`

```python
async def run_agent(task, report_type, report_source, source_urls, ...):
    """Main entry point for research execution."""
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

### 3. Research Phase

**File:** `gpt_researcher/agent.py`

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

### 4. Sub-Query Processing

**File:** `gpt_researcher/skills/researcher.py`

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

### 5. Report Generation

**File:** `gpt_researcher/actions/report_generation.py`

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
    """Generate report using LLM."""
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
