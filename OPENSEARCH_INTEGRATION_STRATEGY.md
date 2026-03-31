# OpenSearch Integration Strategy for GPT-Researcher Deep Research

## Executive Summary

This document presents all viable strategies for integrating an OpenSearch index (containing data from PDFs, CSVs, and Postgres) into the LangGraph-based deep research pipeline. The goal is to produce research reports that combine web search results with internal enterprise data, with clear citation attribution showing whether each claim came from a web source, PDF, CSV, or database record.

---

## Current Architecture Overview

### How Deep Research Works Today

The LangGraph deep research pipeline (`deep_researcher_langgraph/`) executes a **DFS tree search** with 7 nodes:

```
generate_research_plan → generate_search_queries → execute_research
    → fan_out_branches → pick_next_branch → (loop back)
    → assemble_final_context → generate_report → END
```

**Key architectural facts:**

1. **`execute_research`** spawns one `GPTResearcher` per query, hardcoded to `report_source=ReportSource.Web.value` (`nodes.py:287`)
2. **Retrievers** (Tavily, Google, Bing, etc.) return `[{"href": url, "body": snippet}]` — the `body` is discarded, only `href` URLs are scraped
3. **MCP Retriever** is the exception — its results bypass scraping and are injected directly as context
4. **State accumulation** uses `Annotated` reducers: `all_learnings` (list concat), `all_citations` (dict merge), etc.
5. **Citations** are stored as `Dict[str, str]` mapping `insight_text → source_url` — no source type metadata exists
6. **`ReportSource` enum** has: `Web`, `Local`, `Hybrid`, `Azure`, `LangChainDocuments`, `LangChainVectorStore`, `Static` — no `OpenSearch`

### Retriever Interface Contract

Every retriever must implement:
```python
class SomeRetriever:
    def __init__(self, query: str, query_domains=None, **kwargs):
        ...
    def search(self, max_results: int = N) -> List[Dict]:
        # Returns [{"href": "...", "body": "...", "title": "..."}]
        ...
```

Auto-discovery: creating a directory `gpt_researcher/retrievers/opensearch/` makes it discoverable by `get_all_retriever_names()` (`retrievers/utils.py:80`).

---

## Strategy 1: OpenSearch as a Custom Retriever (Retriever-Level Integration)

### Description

Create `gpt_researcher/retrievers/opensearch/opensearch.py` implementing the standard retriever interface. Configure via `RETRIEVER=tavily,opensearch` so both web and OpenSearch retrievers run for every query.

### How It Works

```
generate_search_queries → execute_research
                              ↓
                    GPTResearcher per query
                              ↓
                    get_retrievers() returns [TavilySearch, OpenSearchRetriever]
                              ↓
                    Both retrievers called in _search_relevant_source_urls()
                              ↓
                    URLs from both sources scraped + compressed
                              ↓
                    LLM extracts learnings + citations
```

### Implementation

| File | Change |
|------|--------|
| `gpt_researcher/retrievers/opensearch/__init__.py` | New package |
| `gpt_researcher/retrievers/opensearch/opensearch.py` | New retriever class |
| `gpt_researcher/actions/retriever.py` | Add `case "opensearch":` in `get_retriever()` |
| `gpt_researcher/retrievers/__init__.py` | Export `OpenSearchRetriever` |

The retriever reads `OPENSEARCH_HOST`, `OPENSEARCH_INDEX`, `OPENSEARCH_API_KEY` from env vars and translates the research query into an OpenSearch query (full-text search, semantic search, or both).

### Citation Strategy

Return OpenSearch results with synthetic `href` values that encode source metadata:

```python
def search(self, max_results=10):
    results = self.client.search(index=self.index, body=query_body)
    return [
        {
            "href": f"opensearch://{self.index}/{hit['_id']}?source_type={hit['_source'].get('origin', 'unknown')}",
            "body": hit["_source"]["content"][:500],
            "title": hit["_source"].get("title", "Internal Document"),
        }
        for hit in results["hits"]["hits"][:max_results]
    ]
```

The `opensearch://` URI scheme makes it visually obvious in the report which claims come from internal sources. The `source_type` parameter (`pdf`, `csv`, `postgres`) is embedded in the URI.

### Pros

| Advantage | Details |
|-----------|---------|
| **Minimal code changes** | ~3 files modified, 1 new file created. No changes to LangGraph graph, state, or nodes |
| **Automatic DFS integration** | Every depth level and every branch automatically queries both web and OpenSearch |
| **Uses existing infrastructure** | All scraping, compression, LLM extraction, and citation logic works as-is |
| **Configuration-driven** | Enable/disable via env var `RETRIEVER=tavily,opensearch` — no code deploy needed |
| **Backward compatible** | Existing users are unaffected unless they set the env var |

### Cons

| Disadvantage | Details |
|--------------|---------|
| **Scraping problem** | The pipeline extracts `href` then scrapes the URL. OpenSearch `href` values aren't scrapable web URLs. Requires either: (a) making OpenSearch docs available via HTTP, or (b) modifying `_search_relevant_source_urls()` to detect `opensearch://` URIs and pass their `body` content directly |
| **No source-type awareness** | The LLM extraction prompt has no concept of "this came from a PDF vs web". Citations are just URLs — the `opensearch://` scheme is a workaround, not a first-class feature |
| **Query translation gap** | Web search queries (natural language) may not be optimal for OpenSearch (structured/keyword queries). The same query goes to both retrievers |
| **Breadth dilution** | With 2 retrievers, the same `breadth` count is shared. If breadth=4, each retriever gets ~2 result slots, reducing depth of coverage per source |

### Verdict

**Best for:** Quick proof-of-concept. Good when OpenSearch documents are also accessible via HTTP URLs (e.g., an internal document portal).

---

## Strategy 2: Parallel Graph Node (Graph-Level Integration)

### Description

Add a new LangGraph node `execute_opensearch_research` that runs **in parallel** with the existing `execute_research`. Both nodes write to the same accumulator fields. LangGraph's `Annotated` reducers automatically merge the results.

### How It Works

```
                    generate_search_queries
                         /              \
                        /                \
          execute_research      execute_opensearch_research
          (web via GPTResearcher)   (OpenSearch direct query)
                        \                /
                         \              /
                    merge_results (or implicit via reducers)
                              ↓
                    should_continue_deeper?
                              ↓
                    (rest of DFS continues as normal)
```

### Implementation

| File | Change |
|------|--------|
| `deep_researcher_langgraph/state.py` | Add `source_types: Annotated[Dict[str, str], _merge_dicts]` field |
| `deep_researcher_langgraph/nodes.py` | Add `execute_opensearch_research()` node function |
| `deep_researcher_langgraph/graph.py` | Fan-out from `generate_search_queries` to both nodes; add merge node before `should_continue_deeper` |
| `deep_researcher_langgraph/schemas.py` | Add `source_type: Optional[str]` to `LearningItem` |
| `deep_researcher_langgraph/prompts.py` | Add `PROCESS_OPENSEARCH_RESULTS_PROMPT` with source-type instructions |

The new node:
```python
async def execute_opensearch_research(state: DeepResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Query OpenSearch index and extract learnings with source-type attribution."""
    search_queries = state["search_queries"]
    os_client = _get_opensearch_client(config)
    
    new_learnings = []
    new_citations = {}
    new_source_types = {}
    
    for sq in search_queries:
        # Translate research query → OpenSearch query
        os_results = await os_client.search(sq["query"])
        
        # Build context from OpenSearch hits
        context = format_opensearch_results(os_results)  # includes source_type per hit
        
        # LLM extraction with source-type awareness
        analysis = await extract_learnings_with_source_type(context, llm_service)
        
        for item in analysis.learnings:
            new_learnings.append(item.insight)
            new_citations[item.insight] = item.source_url
            new_source_types[item.insight] = item.source_type  # "pdf", "csv", "postgres"
    
    return {
        "all_learnings": new_learnings,
        "all_citations": new_citations,
        "source_types": new_source_types,
        "research_results": format_as_research_results(os_results),
    }
```

### Citation Strategy

Add a `source_types` field to state that tracks the origin of each learning:

```python
# In state.py
source_types: Annotated[Dict[str, str], _merge_dicts]
# Maps: "insight text" → "web" | "pdf" | "csv" | "postgres"
```

In `assemble_final_context`, format citations with source type:

```python
# Before: f"{learning} [Source: {url}]"
# After:  f"{learning} [Source ({source_type}): {url}]"
```

In the final report, this produces:
> "Revenue grew 15% YoY [Source (postgres): opensearch://financial-data/doc-123]"  
> "Industry analysis confirms this trend [Source (web): https://example.com/report]"

### Pros

| Advantage | Details |
|-----------|---------|
| **True parallel execution** | Web and OpenSearch queries run simultaneously — no added latency |
| **Independent query optimization** | Web queries stay natural language; OpenSearch queries can use DSL, filters, aggregations |
| **First-class source attribution** | Each learning carries `source_type` metadata through the entire pipeline |
| **Clean separation of concerns** | Web and OpenSearch logic are in separate nodes — easy to test, debug, and evolve independently |
| **LangGraph-native** | Uses the framework's built-in fan-out/merge pattern — no hacks |
| **Selective depth control** | Can configure different `breadth` for web vs OpenSearch per depth level |

### Cons

| Disadvantage | Details |
|--------------|---------|
| **Graph complexity** | Adds a parallel fan-out + merge pattern. More nodes, more edges, more conditional logic |
| **State schema changes** | New `source_types` field in `DeepResearchState`. Existing tests need updating |
| **DFS branch interaction** | When `fan_out_branches` creates sub-branches, should sub-branches also query OpenSearch? Need to propagate the source-type decision through the branch stack |
| **Merge ordering** | If both nodes produce conflicting learnings about the same topic, deduplication in `assemble_final_context` may lose source metadata |
| **Prompt engineering** | Need a separate prompt for OpenSearch results that understands structured data (CSV rows, DB records) vs web content |
| **More LLM calls** | Each depth level now makes 2x the LLM extraction calls (one for web, one for OpenSearch) |

### Verdict

**Best for:** Production systems where web and enterprise data are equally important, query optimization matters, and you need first-class source attribution.

---

## Strategy 3: Hybrid ReportSource Mode (GPTResearcher-Level Integration)

### Description

Leverage the existing `ReportSource.Hybrid` pattern in `ResearchConductor` (`researcher.py:161`). This mode already supports loading local documents AND running web search, then merging contexts. Extend it to support OpenSearch as a document source.

### How It Works

```
execute_research node
    ↓
GPTResearcher(report_source="hybrid")
    ↓
ResearchConductor.conduct_research()
    ├── _get_context_by_web_search()    → web_context
    └── DocumentLoader(opensearch)       → docs_context
    ↓
join_local_web_documents(docs_context, web_context)
    ↓
Merged context → LLM extraction → learnings + citations
```

### Implementation

| File | Change |
|------|--------|
| `gpt_researcher/document/document.py` | Add `OpenSearchDocumentLoader` class |
| `gpt_researcher/skills/researcher.py` | Modify `Hybrid` branch to accept OpenSearch as a doc source |
| `gpt_researcher/config/config.py` | Add `OPENSEARCH_*` config variables |
| `deep_researcher_langgraph/nodes.py` | Change `report_source` from `Web` to `Hybrid` in `execute_research` |
| Prompt family | Modify `join_local_web_documents()` to annotate source origins |

### Citation Strategy

The `Hybrid` mode's `join_local_web_documents()` method already separates local and web context. Modify it to prepend source-type headers:

```python
def join_local_web_documents(docs_context, web_context):
    return (
        "=== INTERNAL SOURCES (PDF/CSV/Database) ===\n"
        f"{docs_context}\n\n"
        "=== WEB SOURCES ===\n"
        f"{web_context}"
    )
```

The LLM extraction prompt can then use these headers to attribute source types.

### Pros

| Advantage | Details |
|-----------|---------|
| **Uses proven pattern** | `Hybrid` mode already exists and works. Minimal conceptual risk |
| **No graph changes** | The LangGraph topology stays identical. Only the GPTResearcher config changes |
| **Single LLM call** | Both sources' context is merged BEFORE LLM extraction — one call per query, not two |
| **DocumentLoader ecosystem** | Can reuse existing PDF/DOCX/CSV loaders from `document.py` |
| **Automatic DFS propagation** | Every GPTResearcher instance at every depth level gets both sources automatically |

### Cons

| Disadvantage | Details |
|--------------|---------|
| **Context window pressure** | Both web and OpenSearch contexts are concatenated before LLM processing. With 25K word limit, each source gets less space |
| **Coarse source attribution** | The LLM must infer source type from section headers in the prompt — not guaranteed to be accurate |
| **No independent query optimization** | The same natural-language query goes to both web search and OpenSearch — can't use DSL for OpenSearch |
| **DocumentLoader limitations** | The existing `DocumentLoader` walks a file path. OpenSearch isn't a file path — need a new loader class |
| **Tight coupling** | OpenSearch logic lives inside GPTResearcher, not in the LangGraph layer. Harder to test and evolve independently |
| **All-or-nothing** | Can't selectively enable OpenSearch for certain branches or depth levels |

### Verdict

**Best for:** When you want the simplest possible integration with minimal graph changes and accept that query optimization and source attribution will be approximate.

---

## Strategy 4: MCP Server Wrapper (Protocol-Level Integration)

### Description

Wrap the OpenSearch index as an **MCP (Model Context Protocol) server**. The existing MCP infrastructure in GPTResearcher already handles non-web sources with content passed directly (no scraping). Configure the MCP server endpoint and the existing `mcp_configs` / `mcp_strategy` pipeline handles the rest.

### How It Works

```
execute_research node
    ↓
GPTResearcher(mcp_configs=[opensearch_mcp_config], mcp_strategy="deep")
    ↓
ResearchConductor._execute_mcp_research_for_queries()
    ↓
MCP Server receives query → queries OpenSearch → returns results with content
    ↓
_combine_mcp_and_web_context() merges MCP + web results
    ↓
Context → LLM extraction → learnings + citations
```

### Implementation

| File | Change |
|------|--------|
| External MCP Server | New standalone service wrapping OpenSearch |
| `deep_researcher_langgraph/state.py` | Already has `mcp_configs`, `mcp_strategy` |
| `deep_researcher_langgraph/nodes.py` | Already propagates MCP config to GPTResearcher |
| No graph changes | Everything flows through existing MCP pipeline |

MCP server config:
```python
mcp_configs = [{
    "name": "opensearch-enterprise-data",
    "command": "python",
    "args": ["mcp_opensearch_server.py"],
    "connection_type": "stdio",  # or "sse" for remote
}]
```

### Citation Strategy

The MCP server returns results with structured metadata including source type:
```json
{
    "href": "opensearch://index/doc-id",
    "body": "Full document content...",
    "title": "Q3 Financial Report",
    "metadata": {"source_type": "pdf", "original_file": "q3_report.pdf"}
}
```

MCPRetriever results bypass the scraping pipeline entirely (`researcher.py`), so the full content is preserved. Citations carry the `opensearch://` URI with source type metadata.

### Pros

| Advantage | Details |
|-----------|---------|
| **Zero code changes to GPT-Researcher** | All OpenSearch logic lives in the external MCP server |
| **Content-direct (no scraping)** | MCP results bypass the URL→scrape pipeline — OpenSearch document content is passed directly |
| **Existing infrastructure** | `mcp_configs`, `mcp_strategy`, `MCPRetriever`, `_combine_mcp_and_web_context()` all exist and work |
| **Decoupled deployment** | MCP server can be updated, scaled, or replaced without touching the research pipeline |
| **Rich metadata** | MCP protocol supports structured tool results with arbitrary metadata |
| **Strategy control** | `mcp_strategy="fast"` (once) vs `"deep"` (per-query) gives control over when OpenSearch is queried |

### Cons

| Disadvantage | Details |
|--------------|---------|
| **External service dependency** | Must deploy and maintain a separate MCP server process |
| **MCP protocol overhead** | Tool-call protocol adds latency compared to direct OpenSearch client calls |
| **Limited query control** | MCP tool calls pass a single string query — complex OpenSearch DSL queries require the MCP server to do the translation |
| **Citation format** | MCP results merge into the same citation dict as web results. Source-type attribution depends on URL scheme parsing |
| **Debugging complexity** | Errors span two processes (GPT-Researcher + MCP server). Harder to trace |
| **MCP maturity** | MCP is a relatively new protocol. The GPT-Researcher MCP integration may have edge cases |

### Verdict

**Best for:** When you want zero changes to the GPT-Researcher codebase, have infrastructure to run external services, and want a clean separation between the research engine and the data source.

---

## Strategy 5: Pre-Research OpenSearch Injection (State-Level Integration)

### Description

Add a new LangGraph node `inject_opensearch_context` that runs ONCE at the beginning (after `generate_research_plan`, before the DFS loop). This node queries OpenSearch for the root query, extracts all relevant enterprise data, and injects it into the state's `all_learnings` and `all_context` accumulators. The DFS loop then runs normally with web search only, but the final report includes both pre-injected enterprise data and web-discovered data.

### How It Works

```
generate_research_plan
         ↓
inject_opensearch_context  ← NEW NODE (runs once)
         ↓
generate_search_queries → execute_research → fan_out → (DFS loop)
         ↓
assemble_final_context  ← enterprise + web data merged here
         ↓
generate_report
```

### Implementation

| File | Change |
|------|--------|
| `deep_researcher_langgraph/nodes.py` | Add `inject_opensearch_context()` node |
| `deep_researcher_langgraph/graph.py` | Add node + edge between `generate_research_plan` and `generate_search_queries` |
| `deep_researcher_langgraph/state.py` | Add `source_types` dict field |

### Citation Strategy

The injection node explicitly tags all OpenSearch learnings with source type:

```python
async def inject_opensearch_context(state, config):
    os_results = await query_opensearch(state["query"])
    learnings = []
    citations = {}
    source_types = {}
    
    for doc in os_results:
        learning = extract_key_insight(doc)
        learnings.append(learning)
        citations[learning] = f"opensearch://{doc['_index']}/{doc['_id']}"
        source_types[learning] = doc["_source"].get("origin", "unknown")  # pdf/csv/postgres
    
    return {
        "all_learnings": learnings,
        "all_citations": citations,
        "source_types": source_types,
    }
```

### Pros

| Advantage | Details |
|-----------|---------|
| **Simplest graph change** | One new node, one new edge. No parallel fan-out complexity |
| **No DFS modification** | The entire DFS loop runs unchanged. Enterprise data is pre-loaded |
| **Single OpenSearch query** | Only one round-trip to OpenSearch for the root query — minimal latency |
| **Clean separation** | Enterprise context is established first, then web research fills gaps |
| **Follow-up awareness** | The LLM can generate follow-up questions informed by enterprise data, making web research more targeted |

### Cons

| Disadvantage | Details |
|--------------|---------|
| **No depth-level OpenSearch queries** | Sub-branches at depth N-1 don't query OpenSearch — only the root query does |
| **Stale context at depth** | As the DFS goes deeper into specific subtopics, the pre-injected enterprise data may become less relevant |
| **Context dilution** | Pre-injected enterprise learnings consume part of the 25K word budget, leaving less room for web research |
| **No query refinement** | Can't refine OpenSearch queries based on what web research discovers |
| **Single point of failure** | If the initial OpenSearch query returns poor results, enterprise data is underrepresented in the entire report |

### Verdict

**Best for:** When enterprise data provides background context but the deep research focus is web-based. Good for "ground truth" injection — e.g., internal metrics that web search can't find.

---

## Strategy 6: Dual-Stack DFS (Full Tree-Level Integration)

### Description

The most comprehensive approach. Modify the DFS tree to query BOTH web and OpenSearch at EVERY depth level. Each branch in the `branch_stack` carries a `source_type` indicator. The tree alternates or combines sources at each level.

### How It Works

```
Depth 2: Root Query
├── Web Query 1 ──────── execute_research (web)
│   ├── Web Sub 1.1
│   └── Web Sub 1.2
├── Web Query 2 ──────── execute_research (web)
│   ├── Web Sub 2.1
│   └── Web Sub 2.2
├── OS Query 1 ─────── execute_opensearch (opensearch)
│   ├── OS Sub 1.1
│   └── OS Sub 1.2
└── OS Query 2 ─────── execute_opensearch (opensearch)
    ├── OS Sub 2.1
    └── OS Sub 2.2
```

### Implementation

| File | Change |
|------|--------|
| `deep_researcher_langgraph/state.py` | Add `source_type` to `BranchItem`, add `source_types` accumulator |
| `deep_researcher_langgraph/nodes.py` | Add `execute_opensearch_research()`, modify `generate_search_queries` to generate both web + OS queries, modify `fan_out_branches` to tag branches with source type |
| `deep_researcher_langgraph/graph.py` | Add routing logic: if branch is web → `execute_research`, if opensearch → `execute_opensearch_research` |
| `deep_researcher_langgraph/schemas.py` | Add `source_type` to `SearchQuery`, `LearningItem` |
| `deep_researcher_langgraph/prompts.py` | Add OpenSearch-specific prompts |

The key change is in `generate_search_queries`:
```python
# Generate web queries (half the breadth)
web_queries = generate_web_queries(query, breadth // 2)
# Generate OpenSearch queries (other half)
os_queries = generate_opensearch_queries(query, breadth // 2)
# Tag each with source_type
search_queries = [
    {**q, "source_type": "web"} for q in web_queries
] + [
    {**q, "source_type": "opensearch"} for q in os_queries
]
```

And in the graph, a new conditional edge routes by source type:
```python
workflow.add_conditional_edges(
    "generate_search_queries",
    route_by_source_type,
    {"web": "execute_research", "opensearch": "execute_opensearch_research"}
)
```

### Citation Strategy

Full source-type tracking through the entire tree:

```python
# BranchItem now carries source_type
class BranchItem(TypedDict):
    query: str
    depth: int
    source_type: str  # "web" | "opensearch"

# Learnings carry source metadata
source_types: Annotated[Dict[str, str], _merge_dicts]
# Maps: "insight text" → "web" | "pdf" | "csv" | "postgres"
```

Final report format:
```markdown
## Key Findings

1. Revenue increased 15% YoY driven by enterprise adoption.
   *[Internal Database via OpenSearch — postgres]*

2. Industry analysts project continued growth in the sector.
   *[Web — https://analyst-report.com/2026]*

3. Customer satisfaction scores averaged 4.7/5 in Q4.
   *[Internal Document via OpenSearch — csv]*
```

### Pros

| Advantage | Details |
|-----------|---------|
| **Most comprehensive coverage** | Every depth level queries both web and enterprise data |
| **Independent query optimization** | Web queries use natural language; OpenSearch queries can use DSL, filters, date ranges |
| **Full source attribution** | Every learning, at every depth, carries its source type through the entire pipeline |
| **Proportional depth** | Can control what fraction of breadth goes to web vs OpenSearch per level |
| **Cross-pollination** | Follow-up questions from web research can drive OpenSearch queries, and vice versa |
| **DFS guarantees** | Sub-branches from both sources are processed depth-first, maintaining the same traversal properties |

### Cons

| Disadvantage | Details |
|--------------|---------|
| **Highest complexity** | Significant changes to state, nodes, graph, schemas, and prompts |
| **Doubled query volume** | Every depth level makes queries to both sources — doubles LLM extraction calls |
| **Breadth splitting** | Original breadth is split between sources. With breadth=4: web gets 2, OpenSearch gets 2 |
| **Branch stack complexity** | `BranchItem` now carries source_type. `fan_out_branches` and `pick_next_branch` both need modification |
| **Testing burden** | Significantly more test cases needed — web-only, opensearch-only, mixed, error scenarios |
| **Latency** | More total queries = longer total execution time |

### Verdict

**Best for:** Mission-critical reports where enterprise data is as important as web data, and every subtopic needs both perspectives. Enterprise research platforms.

---

## Comparison Matrix

| Criteria | Strategy 1: Retriever | Strategy 2: Parallel Node | Strategy 3: Hybrid | Strategy 4: MCP | Strategy 5: Pre-Inject | Strategy 6: Dual-Stack |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Code changes** | Minimal | Moderate | Small | Zero (external) | Small | Large |
| **Graph changes** | None | Yes (fan-out) | None | None | 1 node + 1 edge | Significant |
| **Source attribution** | URL-scheme hack | First-class | Prompt-based | URL-scheme | First-class | First-class |
| **Query optimization** | None (same query) | Independent | None | MCP translates | Single shot | Independent |
| **Depth coverage** | Every level | Every level | Every level | Per strategy | Root only | Every level |
| **Latency impact** | +scraping overhead | Parallel (minimal) | +context size | +MCP overhead | +1 query | +doubled queries |
| **Context efficiency** | Standard | 2x extraction | Shared window | Standard | Pre-loaded | 2x extraction |
| **Maintenance** | Low | Medium | Low | Medium (ext svc) | Low | High |
| **Testing complexity** | Low | Medium | Low | Medium | Low | High |
| **Production readiness** | POC | Production | POC+ | Production | Production | Enterprise |

---

## Recommended Strategy

### For Immediate Implementation: Strategy 2 (Parallel Graph Node)

This provides the best balance of:
- **Clean architecture** — separate nodes for separate concerns
- **First-class source attribution** — `source_types` dict in state
- **LangGraph-native** — uses built-in fan-out/merge
- **No latency penalty** — parallel execution
- **Independent query optimization** — OpenSearch queries can use DSL

### For Quick POC: Strategy 1 (Custom Retriever)

If you need something working in a day, creating an OpenSearch retriever is the fastest path. The scraping issue can be worked around by returning full content in `body` and modifying `_search_relevant_source_urls()` to detect the `opensearch://` scheme.

### For Zero Code Changes: Strategy 4 (MCP Server)

If modifying GPT-Researcher is not an option, wrapping OpenSearch as an MCP server requires zero changes to the research pipeline. All complexity lives in the external MCP server.

---

## Citation Implementation (All Strategies)

Regardless of which strategy you choose, the citation system should be enhanced to support source-type attribution. Here is the recommended approach:

### 1. State Enhancement

```python
# In state.py
class DeepResearchState(TypedDict):
    # ... existing fields ...
    source_types: Annotated[Dict[str, str], _merge_dicts]
    # Maps: "insight text" → "web | pdf | csv | postgres"
```

### 2. Learning Extraction Enhancement

```python
# In schemas.py
class LearningItem(BaseModel):
    insight: str
    source_url: Optional[str] = None
    source_type: Optional[str] = None  # NEW: "web", "pdf", "csv", "postgres"
```

### 3. Context Assembly Enhancement

```python
# In nodes.py, assemble_final_context
for learning in all_learnings:
    citation = all_citations.get(learning, "")
    stype = source_types.get(learning, "web")
    if citation:
        context_with_citations.append(
            f"{learning} [Source ({stype}): {citation}]"
        )
```

### 4. Report Prompt Enhancement

```python
# In prompts.py, GENERATE_REPORT_PROMPT
"""
When citing sources, always include the source type in your citations:
- For web sources: [Web: URL]
- For PDF documents: [PDF: document reference]
- For CSV data: [CSV: dataset reference]  
- For database records: [Database: record reference]

This helps the reader understand where each claim originates.
"""
```

---

## OpenSearch Query Translation

The user mentioned they will provide OpenSearch queries later. Here is the interface the integration should expose:

```python
class OpenSearchQueryTranslator:
    """Translates natural language research queries into OpenSearch DSL."""
    
    async def translate(self, research_query: str) -> dict:
        """
        Input: "What was the Q3 revenue growth rate?"
        Output: OpenSearch DSL query body
        """
        # Option A: Direct full-text search
        return {
            "query": {
                "multi_match": {
                    "query": research_query,
                    "fields": ["content", "title", "summary"],
                    "type": "best_fields"
                }
            }
        }
        
        # Option B: LLM-translated structured query (more accurate)
        # Use the strategic LLM to generate OpenSearch DSL from natural language
        
        # Option C: User-provided query templates (most control)
        # The user provides parameterized queries; this method fills in the parameters
```

This component would be plugged into whichever strategy you choose.

---

## Next Steps

1. **Choose a strategy** based on your timeline, source attribution requirements, and maintenance capacity
2. **Provide OpenSearch index schema** — field names, data types, and how PDF/CSV/Postgres origins are tagged
3. **Provide sample OpenSearch queries** — so the query translator can be calibrated
4. **Decide citation format** — how should the final report display internal vs web sources?
5. **Implementation** — I can implement any of the strategies above end-to-end
