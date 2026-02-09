# Core Components & Method Signatures

## Table of Contents
- [GPTResearcher](#gptresearcher)
- [ResearchConductor](#researchconductor)
- [ReportGenerator](#reportgenerator)

---

## GPTResearcher

**File:** `gpt_researcher/agent.py`

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

### Key Methods

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

---

## ResearchConductor

**File:** `gpt_researcher/skills/researcher.py`

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

---

## ReportGenerator

**File:** `gpt_researcher/skills/writer.py`

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
