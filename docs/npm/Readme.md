# GPT Researcher

The gpt-researcher npm package is a WebSocket client for interacting with GPT Researcher.

<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge&theme=clean-inverted&?compact=true)](https://discord.gg/QgZXvJAccX)

[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)

[English](README.md) | [中文](README-zh_CN.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md)

</div>

# 🔎 GPT Researcher

**GPT Researcher is an open deep research agent designed for both web and local research on any given task.** 

The agent produces detailed, factual, and unbiased research reports with citations. GPT Researcher provides a full suite of customization options to create tailor made and domain specific research agents. GPT Researcher goes well beyond RAG: planner and execution agents break each task into research questions, [decision models](https://docs.gptr.dev/docs/gpt-researcher/gptr/context-filter) keep only the context that is actually useful for answering them, [multi-agent](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph) workflows coordinate specialized agents from planning to publication, and [recursive deep research](https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research) explores a topic in both breadth and depth. Research runs in parallel, which keeps it fast, stable and reliable, and reduces misinformation.

**Our mission is to empower individuals and organizations with accurate, unbiased, and factual information through AI.**

## Installation

```bash
npm install gpt-researcher
```

## Usage

### Basic Usage

```javascript
const GPTResearcher = require('gpt-researcher');

const researcher = new GPTResearcher({
  host: 'http://localhost:8000',
  logListener: (data) => console.log('logListener logging data: ',data)
});

researcher.sendMessage({
  query: 'Does providing better context reduce LLM hallucinations?'
});
```


### Log Data Structure

The `logListener` function receives log data with this structure:

```javascript
{
  type: 'logs',
  content: string,    // e.g., 'added_source_url', 'researching', 'scraping_content'
  output: string,     // Human-readable output message
  metadata: any       // Additional data (URLs, counts, etc.)
}
```

Common log content types:

```javascript
'added_source_url': New source URL added
'researching': Research status updates
'scraping_urls': Starting URL scraping
'scraping_content': Content scraping progress
'scraping_images': Image processing updates
'scraping_complete': Scraping completion
'fetching_query_content': Query processing
```

### Parameters

- `task` (required): The research question or task to investigate
- `reportType` (optional): Type of report to generate (default: 'research_report')
- `reportSource` (optional): Source of the report data (default: 'web')
- `tone` (optional): Tone of the report
- `queryDomains` (optional): Array of domain names to filter search results


### Advanced usage

```javascript
const researcher = new GPTResearcher({
  host: 'http://localhost:8000',
  logListener: (data) => console.log('Log:', data)
});

// Advanced usage with all parameters
researcher.sendMessage({
  task: "What are the latest developments in AI?",
  reportType: "research_report",
  reportSource: "web",
  queryDomains: ["techcrunch.com", "wired.com"]
});