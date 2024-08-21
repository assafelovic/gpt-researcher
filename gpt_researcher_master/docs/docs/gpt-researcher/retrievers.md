# Retrievers

Retrievers are search engines used to find the most relevant documents for a given research task.
You can specify your preferred web search or use any custom retriever of your choice.

## Web Search Engines
GPT Researcher defaults to using the [Tavily](https://app.tavily.com) search engine for retrieving search results. 
But you can also use other search engines by specifying the `RETRIEVER` env var. Please note that each search engine has its own API Key requirements and usage limits.

For example:
```bash
RETRIEVER=bing
```

Thanks to our community, we have integrated the following web search engines:
- [Tavily](https://app.tavily.com) - Default
- [Bing](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) - Env: `RETRIEVER=bing`
- [Google](https://developers.google.com/custom-search/v1/overview) - Env: `RETRIEVER=google`
- [Serp API](https://serpapi.com/) - Env: `RETRIEVER=serpapi`
- [Serper](https://serper.dev/) - Env: `RETRIEVER=serper`
- [Searx](https://searx.github.io/searx/) - Env: `RETRIEVER=searx`
- [Duckduckgo](https://pypi.org/project/duckduckgo-search/) - Env: `RETRIEVER=duckduckgo`
- [Arxiv](https://info.arxiv.org/help/api/index.html) - Env: `RETRIEVER=arxiv`
- [Exa](https://docs.exa.ai/reference/getting-started) - Env: `RETRIEVER=exa`

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

Missing a retriever? Feel free to contribute to this project by submitting issues or pull requests on our [GitHub](https://github.com/assafelovic/gpt-researcher) page.