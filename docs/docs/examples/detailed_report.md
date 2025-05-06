# Detailed Report

## Overview

The `DetailedReport` class inspired by the recent STORM paper, is a powerful component of GPT Researcher, designed to generate comprehensive reports on complex topics. It's particularly useful for creating long-form content that exceeds the typical limits of LLM outputs. This class orchestrates the research process, breaking down the main query into subtopics, conducting in-depth research on each, and combining the results into a cohesive, detailed report.

Located in `backend/report_types/detailed_report.py` in the [GPT Researcher GitHub repository](https://github.com/assafelovic/gpt-researcher), this class leverages the capabilities of the `GPTResearcher` agent to perform targeted research and generate content.

## Key Features

- Breaks down complex topics into manageable subtopics
- Conducts in-depth research on each subtopic
- Generates a comprehensive report with introduction, table of contents, and body
- Avoids redundancy by tracking previously written content
- Supports asynchronous operations for improved performance

## Class Structure

### Initialization

The `DetailedReport` class is initialized with the following parameters:

- `query`: The main research query
- `report_type`: Type of the report
- `report_source`: Source of the report
- `source_urls`: Initial list of source URLs
- `config_path`: Path to the configuration file
- `tone`: Tone of the report (using the `Tone` enum)
- `websocket`: WebSocket for real-time communication
- `subtopics`: Optional list of predefined subtopics
- `headers`: Optional headers for HTTP requests

## How It Works

1. The `DetailedReport` class starts by conducting initial research on the main query.
2. It then breaks down the topic into subtopics.
3. For each subtopic, it:
   - Conducts focused research
   - Generates draft section titles
   - Retrieves relevant previously written content to avoid redundancy
   - Writes a report section
4. Finally, it combines all subtopic reports, adds a table of contents, and includes source references to create the final detailed report.

## Usage Example

Here's how you can use the `DetailedReport` class in your project:

```python
import asyncio
from fastapi import WebSocket
from gpt_researcher.utils.enum import Tone
from backend.report_type import DetailedReport

async def generate_report(websocket: WebSocket):
    detailed_report = DetailedReport(
        query="The impact of artificial intelligence on modern healthcare",
        report_type="research_report",
        report_source="web_search",
        source_urls=[],  # You can provide initial source URLs if available
        config_path="path/to/config.yaml",
        tone=Tone.FORMAL,
        websocket=websocket,
        subtopics=[],  # You can provide predefined subtopics if desired
        headers={}  # Add any necessary HTTP headers
    )

    final_report = await detailed_report.run()
    return final_report

# In your FastAPI app
@app.websocket("/generate_report")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    report = await generate_report(websocket)
    await websocket.send_text(report)
```

This example demonstrates how to create a `DetailedReport` instance and run it to generate a comprehensive report on the impact of AI on healthcare.

## Conclusion

The `DetailedReport` class is a sophisticated tool for generating in-depth, well-structured reports on complex topics. By breaking down the main query into subtopics and leveraging the power of GPT Researcher, it can produce content that goes beyond the typical limitations of LLM outputs. This makes it an invaluable asset for researchers, content creators, and anyone needing detailed, well-researched information on a given topic.