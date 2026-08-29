# Exclude Terms

The `search_exclude_terms` feature lets you exclude specific terms from search results by appending Google-style exclusion operators to the query string before it is sent to the search engine.

## Usage

Pass a list of terms when constructing `GPTResearcher`:

```python
researcher = GPTResearcher(
    query="PC sales in 2012",
    search_exclude_terms=["gartner", "market share"],
)
```

The query sent to the search engine becomes:

```
PC sales in 2012 -gartner -"market share"
```

Single-word terms get a leading `-`. Multi-word terms are wrapped in quotes (`-"multi word"`). If a multi-word term itself contains double quotes it is wrapped in single quotes instead.

## Supported Retrievers

| Retriever | Status |
|---|---|
| DuckDuckGo | Supported |
| Google (Custom Search) | Supported |
| Brave Search | Supported |
| Serper | Supported |
| SerpAPI | Supported |
| SearchApi | Supported |
| SearxNG | Supported |

All supported retrievers use the same Google-style `-term` exclusion syntax, which is honored by their underlying search engines.

## Unsupported Retrievers

When `search_exclude_terms` is configured with an unsupported retriever, a warning is logged and the search proceeds without exclusion.

| Retriever | Reason |
|---|---|
| **Bing** | The Bing Web Search API deprecated advanced query operators (`-term`, `site:`, etc.). Appending `-term` would be treated as literal text and degrade query relevance. |
| **BoCha** | No documented operator support in the BoCha API. |
| **Tavily** | Tavily uses natural-language queries; its API only offers `exclude_domains` for domain-level filtering. Operator syntax is not interpreted. |
| **Exa** | Exa performs neural/semantic search by default and does not support boolean exclusion operators. |
| **arXiv** | Uses its own query language (fielded terms like `ti:`, `au:`, boolean `AND`/`NOT`). Generic `-term` syntax is not applicable; scholarly metadata search rarely benefits from term exclusion. |
| **Semantic Scholar** | Domain-specific query API with its own syntax; term exclusion operators are not supported. |
| **PubMed Central** | Uses Entrez E-Search with MEDLINE indexing terms; a fundamentally different query model. |
| **OpenAlex** | Uses `?search=` text-matching parameter without boolean operator support. |
| **GetXAPI / Xquik** | X/Twitter advanced search has its own operator semantics distinct from web-search exclusion. |
| **fastCRW (crw)** | Aggregator/passthrough API without documented term-exclusion support. |
| **GroundRoute** | Multi-engine router; exclusion would need to be handled by the underlying engine selection, not the query string. |
| **Custom** | User-defined endpoint — exclusion semantics belong to the endpoint implementation. |
| **MCP** | Separate instantiation path; tool-driven research with no free-text query to modify. |

## Runtime Behavior

- **Empty or unset**: When `search_exclude_terms` is not provided (default), retrievers behave exactly as if the feature did not exist — no kwarg is passed, no query modification occurs.
- **Configured + supported retriever**: Exclusion operators are appended to the query string before the search request.
- **Configured + unsupported retriever**: A warning is logged (`<RetrieverName> does not support exclude_terms; ignoring`) and the search proceeds with the original query.
