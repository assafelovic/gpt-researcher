# Retriever System Reference

## Table of Contents
- [Available Retrievers](#available-retrievers)
- [Retriever Selection](#retriever-selection)
- [Adding a New Retriever](#adding-a-new-retriever)

---

## Available Retrievers

**Directory:** `gpt_researcher/retrievers/`

| Retriever | Class | API Key Env Var |
|-----------|-------|-----------------|
| Tavily | `TavilySearch` | `TAVILY_API_KEY` |
| Google | `GoogleSearch` | `GOOGLE_API_KEY`, `GOOGLE_CX_KEY` |
| Bing | `BingSearch` | `BING_API_KEY` |
| Brave | `BraveSearch` | `BRAVE_API_KEY` |
| DuckDuckGo | `Duckduckgo` | None |
| SearX | `SearxSearch` | `SEARX_URL` |
| Serper | `SerperSearch` | `SERPER_API_KEY` |
| SerpAPI | `SerpApiSearch` | `SERPAPI_API_KEY` |
| SearchAPI | `SearchApiSearch` | `SEARCHAPI_API_KEY` |
| Exa | `ExaSearch` | `EXA_API_KEY` |
| GroundRoute | `GroundRouteSearch` | `GROUNDROUTE_API_KEY` |
| fastCRW | `CRWRetriever` | `CRW_API_KEY` |
| BoCha | `BoChaSearch` | `BOCHA_API_KEY` |
| Xquik | `XquikSearch` | `XQUIK_API_KEY` |
| GetXAPI (X/Twitter) | `GetXAPISearch` | `GETXAPI_API_KEY` |
| arXiv | `ArxivSearch` | None |
| Semantic Scholar | `SemanticScholarSearch` | None |
| PubMed Central | `PubMedCentralSearch` | None |
| OpenAlex | `OpenAlexSearch` | `OPENALEX_API_KEY`, `OPENALEX_EMAIL` |
| MCP | `MCPRetriever` | Per-server |
| Custom | `CustomRetriever` | User-defined |

> The authoritative list is the `match` statement in `gpt_researcher/actions/retriever.py` (`get_retriever`).

---

## Retriever Selection

**File:** `gpt_researcher/actions/retriever.py`

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

def get_retrievers(headers: dict[str, str], cfg) -> list:
    """
    Resolve which retriever(s) to use, in priority order:
    headers["retrievers"] / headers["retriever"] → cfg.retrievers / cfg.retriever
    → default (TavilySearch). Accepts a comma-separated string or a list.

    Usage: RETRIEVER=tavily,google,mcp
    """
    # ... resolve names from headers/cfg (see actions/retriever.py) ...
    # Invalid names fall back to get_default_retriever():
    return [get_retriever(r) or get_default_retriever() for r in retriever_names]
```

---

## Adding a New Retriever

### Step 1: Create Retriever File

**File:** `gpt_researcher/retrievers/my_retriever/my_retriever.py`

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

### Step 2: Register in retriever.py

**File:** `gpt_researcher/actions/retriever.py`

```python
case "my_retriever":
    from gpt_researcher.retrievers.my_retriever import MyRetriever
    return MyRetriever
```

### Step 3: Export in __init__.py

**File:** `gpt_researcher/retrievers/__init__.py`

```python
from .my_retriever import MyRetriever
__all__ = [..., "MyRetriever"]
```

### Step 4: Usage

```bash
RETRIEVER=tavily,my_retriever
```

```python
researcher = GPTResearcher(
    query="...",
    # Will use both Tavily and your custom retriever
)
```
