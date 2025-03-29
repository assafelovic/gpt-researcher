---
sidebar_position: 2
---

# Advanced Usage

This guide covers advanced usage scenarios and configurations for the GPT Researcher MCP Server.

## Custom Configuration

You can customize the MCP server behavior by modifying various configuration parameters:

### Environment Variables

Create a `.env` file with additional configuration options:

```bash
# Required API keys
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key

# Optional configurations assuming using OpenAI
STRATEGIC_LLM=openai:gpt-4o-mini # Change default to faster reasoning model
MAX_ITERATIONS=2 # Make the research faster by reducing iterations
SCRAPER=tavily_extract # For production use, using hosted scraping methods (assuming you use tavily)
```

### Server Configuration File

You can create a `config.json` file to customize server behavior:

```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "debug": false,
  "timeout": 300,
  "max_concurrent_requests": 10
}
```

## Integrating with Claude

To integrate with Claude effectively:

1. Make sure your Claude model has MCP capabilities enabled
2. Point Claude to the MCP server endpoint
3. Use the appropriate prompts to guide Claude in using the research tools

Example configuration for Claude:

```json
{
  "tools": [
    {
      "name": "gptr-researcher",
      "endpoint": "http://localhost:8000/mcp"
    }
  ]
}
```

## Advanced Tool Usage

### Conducting Deep Research

For deeper research capabilities:

```
Use the conduct_research tool with these advanced parameters:
{
  "query": "quantum computing advancements 2024",
  "depth": "deep",
  "focus_areas": ["hardware", "algorithms", "applications"],
  "timeline": "last 1 year"
}
```

### Customizing Report Generation

The write_report tool accepts several customization options:

```
Use the write_report tool with:
{
  "style": "academic",
  "format": "markdown",
  "include_images": true,
  "citation_style": "APA",
  "executive_summary": true
}
```

## Securing Your MCP Server

To secure your MCP server deployment:

1. Add API key authentication:
   ```python
   # Add to server.py
   @app.middleware("http")
   async def verify_api_key(request, call_next):
       api_key = request.headers.get("X-API-Key")
       if api_key != os.getenv("MCP_API_KEY"):
           return JSONResponse(status_code=401, content={"error": "Invalid API key"})
       return await call_next(request)
   ```

2. Enable HTTPS:
   ```bash
   # Run with HTTPS
   uvicorn server:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
   ```

3. Set up rate limiting:
   ```python
   # Add rate limiting
   from fastapi import Depends, HTTPException
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   @app.post("/mcp")
   @limiter.limit("10/minute")
   async def mcp_endpoint(request: Request, payload: dict):
       # Endpoint code
   ```

## Deploying with Docker

For easy deployment with Docker:

1. Create a Dockerfile:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server.py"]
```

2. Build and run the Docker container:
```bash
docker build -t gpt-researcher-mcp .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key -e TAVILY_API_KEY=your_key gpt-researcher-mcp
```

## Monitoring and Logging

Enable detailed logging to monitor server activity:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("mcp_server")
```

## Extending Functionality

You can extend the MCP server with additional capabilities:

1. Add new research tools
2. Implement custom report formats
3. Integrate with additional data sources
4. Add specialized research agents

For example, to add a new tool:

```python
@app.tool("analyze_sentiment")
async def analyze_sentiment(query: str):
    """Analyze the sentiment of research results."""
    # Implementation
    return {"sentiment": "positive", "confidence": 0.87}
```

## Troubleshooting Advanced Issues

### Handling Rate Limits

If you encounter rate limits with external APIs:

```python
import time
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
def search_with_retry(query):
    try:
        return search_engine.search(query)
    except RateLimitError:
        time.sleep(5)
        raise
```

### Memory Management

For handling large research tasks:

```python
import gc

def clean_memory():
    """Force garbage collection to free memory"""
    gc.collect()
```

## Next Steps

- Explore [integrating with your own applications](../frontend/introduction)
- Learn about [creating custom agents](../multi_agents/langgraph) to enhance research capabilities
- Contribute to the [GPT Researcher project](../../contribute)

:-) 