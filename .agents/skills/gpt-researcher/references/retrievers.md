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
