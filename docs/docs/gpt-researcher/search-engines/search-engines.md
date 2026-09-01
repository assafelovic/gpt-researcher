# Search Engines

Search Engines are used to find the most relevant web sources and content for a given research task.
You can specify your preferred web search or use any custom retriever of your choice.

## Web Search Engines

GPT Researcher defaults to using the [Tavily](https://app.tavily.com) search engine for retrieving search results.
But you can also use other search engines by specifying the `RETRIEVER` env var. Please note that each search engine has its own API Key requirements and usage limits.

For example:

```bash
RETRIEVER=bing
```

You can also specify multiple retrievers by separating them with commas. The system will use each specified retriever in sequence.
For example:

```bash
RETRIEVER=tavily,arxiv
```

For academic literature reviews, combine a broad web retriever with scholarly retrievers:

```bash
RETRIEVER=tavily,openalex,semantic_scholar
```

Thanks to our community, we have integrated the following web search engines and research retrievers:

- [Tavily](https://app.tavily.com) - Default
- [Bing](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) - Env: `RETRIEVER=bing`
- [Brave Search](https://brave.com/search/api/) - Env: `RETRIEVER=brave` and `BRAVE_API_KEY`
- [GroundRoute](https://groundroute.ai/) - Env: `RETRIEVER=groundroute` and `GROUNDROUTE_API_KEY`
- [BoCha](https://bochaai.com/) - Env: `RETRIEVER=bocha` and `BOCHA_API_KEY`
- [Google](https://developers.google.com/custom-search/v1/overview) - Env: `RETRIEVER=google`
- [SearchApi](https://www.searchapi.io/) - Env: `RETRIEVER=searchapi`
- [Serp API](https://serpapi.com/) - Env: `RETRIEVER=serpapi`
- [Serper](https://serper.dev/) - Env: `RETRIEVER=serper` - [Setup Guide](#serper)
- [Searx](https://searx.github.io/searx/) - Env: `RETRIEVER=searx`
- [Duckduckgo](https://pypi.org/project/duckduckgo-search/) - Env: `RETRIEVER=duckduckgo`
- [Arxiv](https://info.arxiv.org/help/api/index.html) - Env: `RETRIEVER=arxiv`
- [OpenAlex](https://docs.openalex.org/) - Env: `RETRIEVER=openalex`; optional `OPENALEX_EMAIL` and `OPENALEX_API_KEY`
- [Semantic Scholar](https://www.semanticscholar.org/product/api) - Env: `RETRIEVER=semantic_scholar`
- [Exa](https://docs.exa.ai/reference/getting-started) - Env: `RETRIEVER=exa`
- [fastCRW](https://fastcrw.com/docs/rest-api) - Env: `RETRIEVER=crw`
- [PubMedCentral](https://www.ncbi.nlm.nih.gov/home/develop/api/) - Env: `RETRIEVER=pubmed_central`
- [Xquik](https://xquik.com/) - Env: `RETRIEVER=xquik` and `XQUIK_API_KEY`
- [MCP](../retrievers/mcp-configs) - Env: `RETRIEVER=mcp`

## Custom Retrievers

You can also use any custom retriever of your choice by specifying the `RETRIEVER=custom` env var.
Custom retrievers allow you to use any search engine that provides an API to retrieve documents and is widely used for enterprise research tasks.

In addition to setting the `RETRIEVER` env, you also need to set the following env vars:

- `RETRIEVER_ENDPOINT`: The endpoint URL of the custom retriever.
- Additional arguments required by the retriever should be prefixed with `RETRIEVER_ARG_` (e.g., RETRIEVER_ARG_API_KEY).

### Example

```bash
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://api.myretriever.com
RETRIEVER_ARG_API_KEY=YOUR_API_KEY
```

### Response Format

For the custom retriever to work correctly, the response from the endpoint should be in the following format:

```json
[
  {
    "url": "http://example.com/page1",
    "raw_content": "Content of page 1"
  },
  {
    "url": "http://example.com/page2",
    "raw_content": "Content of page 2"
  }
]
```

The system assumes this response format and processes the list of sources accordingly.

## Search Engine Configuration

### Brave Search

To use [Brave Search](https://brave.com/search/api/) as your search engine:

1. Get your API key from [Brave Search API](https://brave.com/search/api/)
2. Set the required environment variables:

```bash
RETRIEVER=brave
BRAVE_API_KEY=your_api_key_here
```

### Serper

To use [Serper](https://serper.dev/) as your search engine:

1. Get your API key from [serper.dev](https://serper.dev/)
2. Set the required environment variables:

```bash
RETRIEVER=serper
SERPER_API_KEY=your_api_key_here
```

**Optional Configuration:**

```bash
SERPER_REGION=us                    # Country code (us, kr, jp, etc.)
SERPER_LANGUAGE=en                  # Language code (en, ko, ja, etc.)
SERPER_TIME_RANGE=qdr:w            # Time filter (qdr:h, qdr:d, qdr:w, qdr:m, qdr:y)
SERPER_EXCLUDE_SITES=youtube.com   # Exclude sites (comma-separated)
```

### OpenAlex

To use [OpenAlex](https://docs.openalex.org/) for scholarly works:

```bash
RETRIEVER=openalex
OPENALEX_EMAIL=you@example.com      # Optional but recommended for polite API usage
OPENALEX_API_KEY=your_api_key_here  # Optional; improves rate limits
```

OpenAlex works without an API key, but setting an email or free API key can make larger research runs more reliable.

### PubMed Central

To use PubMed Central full-text retrieval:

```bash
RETRIEVER=pubmed_central
NCBI_API_KEY=your_api_key_here      # Optional; improves NCBI rate limits
PUBMED_DB=pmc                       # Optional; defaults to pmc
```

Missing a retriever? Feel free to contribute to this project by submitting issues or pull requests on our [GitHub](https://github.com/assafelovic/gpt-researcher) page.
