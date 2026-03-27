# Advanced Patterns Reference

## Table of Contents
- [Custom Callbacks](#custom-callbacks)
- [Custom WebSocket Handler](#custom-websocket-handler)
- [LangChain Integration](#langchain-integration)
- [Search Restrictions](#search-restrictions)
- [Error Handling Patterns](#error-handling-patterns)

---

## Custom Callbacks

```python
def cost_callback(cost: float):
    print(f"API call cost: ${cost}")

researcher = GPTResearcher(query="...")
researcher.add_costs = cost_callback  # Override cost tracking
```

---

## Custom WebSocket Handler

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

---

## LangChain Integration

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

---

## Search Restrictions

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
