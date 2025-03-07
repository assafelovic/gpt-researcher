# Structured JSON Responses

This document explains how to use the structured JSON response functionality in GPT Researcher.

## Overview

The structured JSON response functionality allows you to get responses from language models in a structured format defined by Pydantic models. This ensures that the responses are properly typed and validated, making it easier to work with the data programmatically.

## How It Works

1. Define a Pydantic model that represents the structure of the response you want.
2. Use the `get_structured_response` method to get a response in that format.
3. The method will handle the details of prompting the model to return JSON and parsing the response.

## Example

```python
import asyncio
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.config.config import Config
from gpt_researcher.utils.structured_models import ResearchSummary

async def main():
    # Initialize the researcher
    cfg = Config()
    query = "What are the latest advancements in quantum computing?"
    researcher = GPTResearcher(query=query, config=cfg)
    
    # Create the messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful research assistant that provides structured information about topics."
        },
        {
            "role": "user",
            "content": f"Provide a structured summary of research on: {query}."
        }
    ]
    
    # Get a structured response
    result = await researcher.context_manager.get_structured_response(
        messages=messages,
        response_model=ResearchSummary,
    )
    
    # Use the structured response
    print(f"Query: {result.query}")
    print(f"Main Findings: {result.main_findings}")
    print(f"Number of sources: {len(result.sources)}")
    
    # Export as JSON
    json_data = result.model_dump_json(indent=2)
    print(json_data)

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Models

The `structured_models.py` module provides a variety of pre-defined Pydantic models for common use cases:

- `TextAnalysis`: For analyzing text (sentiment, key points, entities, summary)
- `SearchResults`: For search results with relevance scores
- `FactCheckResult`: For fact-checking claims
- `QAResults`: For question-answering
- `Tutorial`: For step-by-step tutorials
- `CodeSolution`: For code solutions with explanations
- `Comparison`: For comparing multiple items
- `ResearchSummary`: For research summaries with sources
- `Debate`: For presenting balanced arguments on a topic
- `Recommendations`: For providing recommendations

## Creating Custom Models

You can create your own Pydantic models for custom structured responses:

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class CustomResult(BaseModel):
    """A custom result model."""
    title: str = Field(description="The title of the result")
    items: List[str] = Field(description="List of items")
    score: Optional[float] = Field(None, description="Optional score")

# Use it with get_structured_response
result = await researcher.context_manager.get_structured_response(
    messages=messages,
    response_model=CustomResult,
)
```

## How It Works Under the Hood

The `get_structured_response` method:

1. Adds a system message instructing the model to return JSON in the specified format
2. Uses provider-specific methods to request JSON output:
   - For OpenAI-compatible models: Uses the `response_format` parameter
   - For other models: Uses function calling or similar mechanisms
3. Parses the response into the specified Pydantic model
4. Handles errors and retries if necessary

## Benefits

- **Type Safety**: Responses are properly typed and validated
- **Consistency**: Ensures consistent response format
- **Error Handling**: Robust parsing with multiple fallback mechanisms
- **Compatibility**: Works with different LLM providers
- **Reusability**: Pre-defined models for common use cases 