# Hybrid Research

## Introduction

GPT Researcher can combine web search capabilities with local document analysis to provide comprehensive, context-aware research results. 

This guide will walk you through the process of setting up and running hybrid research using GPT Researcher.

## Prerequisites

Before you begin, ensure you have the following:

- Python 3.10 or higher installed on your system
- pip (Python package installer)
- An OpenAI API key (you can also choose other supported [LLMs](../gpt-researcher/llms/llms.md))
- A Tavily API key (you can also choose other supported [Retrievers](../gpt-researcher/search-engines/retrievers.md))

## Installation

```bash
pip install gpt-researcher
```

## Setting Up the Environment

Export your API keys as environment variables:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
export TAVILY_API_KEY=your_tavily_api_key_here
```

For custom OpenAI-compatible APIs, you can also set:

```bash
export OPENAI_BASE_URL=your_custom_api_base_url_here
```

Alternatively, you can set these in your Python script:

```python
import os
os.environ['OPENAI_API_KEY'] = 'your_openai_api_key_here'
os.environ['TAVILY_API_KEY'] = 'your_tavily_api_key_here'
os.environ['OPENAI_BASE_URL'] = 'your_custom_api_base_url_here'  # Optional
```
Set the environment variable REPORT_SOURCE to an empty string "" in default.py
## Preparing Documents

### 1. Local Documents
1. Create a directory named `my-docs` in your project folder.
2. Place all relevant local documents (PDFs, TXTs, DOCXs, etc.) in this directory.

### 2. Online Documents
1. Here is an example of your online document URL example: https://xxxx.xxx.pdf (supports file formats like PDFs, TXTs, DOCXs, etc.) 


## Running Hybrid Research By "Local Documents"

Here's a basic script to run hybrid research:

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_research_report(query: str, report_type: str, report_source: str) -> str:
    researcher = GPTResearcher(query=query, report_type=report_type, report_source=report_source)
    research = await researcher.conduct_research()
    report = await researcher.write_report()
    return report

if __name__ == "__main__":
    query = "How does our product roadmap compare to emerging market trends in our industry?"
    report_source = "hybrid"

    report = asyncio.run(get_research_report(query=query, report_type="research_report", report_source=report_source))
    print(report)
```

## Running Hybrid Research By "Online Documents"

Here's a basic script to run hybrid research:

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_research_report(query: str, report_type: str, report_source: str) -> str:
    researcher = GPTResearcher(query=query, report_type=report_type, document_urls=document_urls, report_source=report_source)
    research = await researcher.conduct_research()
    report = await researcher.write_report()
    return report

if __name__ == "__main__":
    query = "How does our product roadmap compare to emerging market trends in our industry?"
    report_source = "hybrid"
    document_urls = ["https://xxxx.xxx.pdf", "https://xxxx.xxx.doc"]

    report = asyncio.run(get_research_report(query=query, report_type="research_report", document_urls=document_urls, report_source=report_source))
    print(report)
```

To run the script:

1. Save it as `run_research.py`
2. Execute it with: `python run_research.py`

## Understanding the Results

The output will be a comprehensive research report that combines insights from both web sources and your local documents. The report typically includes an executive summary, key findings, detailed analysis, comparisons between your internal data and external trends, and recommendations based on the combined insights.

## Troubleshooting

1. **API Key Issues**: Ensure your API keys are correctly set and have the necessary permissions.
2. **Document Loading Errors**: Check that your local documents are in supported formats and are not corrupted.
3. **Memory Issues**: For large documents or extensive research, you may need to increase your system's available memory or adjust the `chunk_size` in the document processing step.

## FAQ

**Q: How long does a typical research session take?**
A: The duration varies based on the complexity of the query and the amount of data to process. It can range from 1-5 minutes for very comprehensive research.

**Q: Can I use GPT Researcher with other language models?**
A: Currently, GPT Researcher is optimized for OpenAI's models. Support for other models can be found [here](../gpt-researcher/llms/llms.md).

**Q: How does GPT Researcher handle conflicting information between local and web sources?**
A: The system attempts to reconcile differences by providing context and noting discrepancies in the final report. It prioritizes more recent or authoritative sources when conflicts arise.

**Q: Is my local data sent to external servers during the research process?**
A: No, your local documents are processed on your machine. Only the generated queries and synthesized information (not raw data) are sent to external services for web research.

For more information and updates, please visit the [GPT Researcher GitHub repository](https://github.com/assafelovic/gpt-researcher).
