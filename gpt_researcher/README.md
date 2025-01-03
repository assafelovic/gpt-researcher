# 🔎 GPT Researcher
[![Official Website](https://img.shields.io/badge/Official%20Website-gptr.dev-blue?style=for-the-badge&logo=world&logoColor=white)](https://gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge)](https://discord.com/invite/QgZXvJAccX)

[![GitHub Repo stars](https://img.shields.io/github/stars/assafelovic/gpt-researcher?style=social)](https://github.com/assafelovic/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/tavilyai?style=social)](https://twitter.com/tavilyai)
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)

**GPT Researcher is an autonomous agent designed for comprehensive online research on a variety of tasks.** 

The agent can produce detailed, factual and unbiased research reports, with customization options for focusing on relevant resources, outlines, and lessons. Inspired by the recent [Plan-and-Solve](https://arxiv.org/abs/2305.04091) and [RAG](https://arxiv.org/abs/2005.11401) papers, GPT Researcher addresses issues of speed, determinism and reliability, offering a more stable performance and increased speed through parallelized agent work, as opposed to synchronous operations.

**Our mission is to empower individuals and organizations with accurate, unbiased, and factual information by leveraging the power of AI.**

#### PIP Package
> **Step 0** - Install Python 3.11 or later. [See here](https://www.tutorialsteacher.com/python/install-python) for a step-by-step guide.
> **Step 1** - install GPT Researcher package [PyPI page](https://pypi.org/project/gpt-researcher/)
```bash
$ pip install gpt-researcher
```
> **Step 2** - Create .env file with your OpenAI Key and Tavily API key or simply export it
```bash
$ export OPENAI_API_KEY={Your OpenAI API Key here}
```
```bash
$ export TAVILY_API_KEY={Your Tavily API Key here}
```
> **Step 3** - Start Coding using GPT Researcher in your own code, example:
```python
from gpt_researcher import GPTResearcher
import asyncio


async def get_report(query: str, report_type: str) -> str:
    researcher = GPTResearcher(query, report_type)
    report = await researcher.run()
    return report

if __name__ == "__main__":
    query = "what team may win the NBA finals?"
    report_type = "research_report"

    report = asyncio.run(get_report(query, report_type))
    print(report)

### Configuration Options

GPT Researcher can be configured in multiple ways:

1. **Environment Variable for Config Path** (Recommended)
```bash
# In your .env file
CONFIG_PATH=configs/my_custom_config.json
```

This will override the default settings with your custom configuration. You can find all available configuration options in the [GPT Researcher 
documentation](https://docs.gptr.dev/docs/gpt-researcher/gptr/config).

2. **Direct JSON Configuration File**
Create a JSON file in the `configs` directory (e.g., `configs/my_custom_config.json`) with your settings:

```json
{
    "RETRIEVER": "tavily",
    "FAST_LLM": "google_genai:gemini-pro",
    "SMART_LLM": "google_genai:gemini-pro",
    // ... other configuration options
    "MAX_ITERATIONS": 3,
    "MAX_SUBTOPICS": 5
}
```

3. **Individual Environment Variables**
```bash
RETRIEVERS=google
FAST_LLM=cohere:command
SMART_LLM=cohere:command-nightly
# ... other environment variables
```

#### Configuration Priority
1. Environment variable `CONFIG_PATH` pointing to a JSON file
2. Individual environment variables
3. Default configuration

A sample configuration file is provided at `configs/sample_config.json` with all available options. You can copy this file and modify it for your needs:

```bash
cp configs/sample_config.json configs/my_custom_config.json
```


## Configuration Usage Examples

### Quick Initialization
You can quickly initialize GPT Researcher with a custom configuration:

```python
from gpt_researcher import GPTResearcher

researcher = GPTResearcher(
    query="What are the latest developments in quantum computing?",
    report_type="research_report",
    config_path="configs/my_custom_config.json"
)
```

### Complete Script Example
For a full implementation including async handling:

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_report(query: str, report_type: str) -> str:
    researcher = GPTResearcher(
        query=query, 
        report_type=report_type,
        config_path="configs/my_custom_config.json"
    )
    await researcher.conduct_research()
    report = await researcher.write_report()
    return report

if __name__ == "__main__":
    query = "What are the latest developments in quantum computing?"
    report_type = "research_report"
    
    report = asyncio.run(get_report(query, report_type))
    print(report)
```

Both methods will use your custom configuration file while maintaining all the default settings for any values not explicitly defined in your config.