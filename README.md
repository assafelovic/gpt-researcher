# 🔎 GPT Researcher
[![Official Website](https://img.shields.io/badge/Official%20Website-gptr.dev-blue?style=for-the-badge&logo=world&logoColor=white)](https://gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/2pFkc83fRq?style=for-the-badge)](https://discord.com/invite/2pFkc83fRq)

[![GitHub Repo stars](https://img.shields.io/github/stars/assafelovic/gpt-researcher?style=social)](https://github.com/assafelovic/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/assafelovic/gpt-researcher?style=for-the-badge&color=orange

-  [English](README.md)
-  [中文](README-zh_CN.md)

**GPT Researcher is an autonomous agent designed for comprehensive online research on a variety of tasks.** 

The agent can produce detailed, factual and unbiased research reports, with customization options for focusing on relevant resources, outlines, and lessons. Inspired by the recent [Plan-and-Solve](https://arxiv.org/abs/2305.04091) and [RAG](https://arxiv.org/abs/2005.11401) papers, GPT Researcher addresses issues of speed, determinism and reliability, offering a more stable performance and increased speed through parallelized agent work, as opposed to synchronous operations.

**Our mission is to empower individuals and organizations with accurate, unbiased, and factual information by leveraging the power of AI.**

## Why GPT Researcher?

- To form objective conclusions for manual research tasks can take time, sometimes weeks to find the right resources and information.
- Current LLMs are trained on past and outdated information, with heavy risks of hallucinations, making them almost irrelevant for research tasks.
- Services that enable web search (such as ChatGPT + Web Plugin), only consider limited sources and content that in some cases result in superficial and biased answers.
- Using only a selection of web sources can create bias in determining the right conclusions for research tasks.

## Demo
https://github.com/assafelovic/gpt-researcher/assets/13554167/dd6cf08f-b31e-40c6-9907-1915f52a7110

## Architecture
The main idea is to run "planner" and "execution" agents, whereas the planner generates questions to research, and the execution agents seek the most related information based on each generated research question. Finally, the planner filters and aggregates all related information and creates a research report. <br /> <br /> 
The agents leverage both gpt3.5-turbo and gpt-4-turbo (128K context) to complete a research task. We optimize for costs using each only when necessary. **The average research task takes around 3 minutes to complete, and costs ~$0.1.**

<div align="center">
<img align="center" height="500" src="https://cowriter-images.s3.amazonaws.com/architecture.png">
</div>


More specifically:
* Create a domain specific agent based on research query or task.
* Generate a set of research questions that together form an objective opinion on any given task. 
* For each research question, trigger a crawler agent that scrapes online resources for information relevant to the given task.
* For each scraped resources, summarize based on relevant information and keep track of its sources.
* Finally, filter and aggregate all summarized sources and generate a final research report.

## Tutorials
 - [How it Works](https://docs.tavily.com/blog/building-gpt-researcher)
 - [How to Install](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [Live Demo](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## Features
- 📝 Generate research, outlines, resources and lessons reports
- 📜 Can generate long and detailed research reports (over 2K words)
- 🌐 Aggregates over 20 web sources per research to form objective and factual conclusions
- 🖥️ Includes an easy-to-use web interface (HTML/CSS/JS)
- 🔍 Scrapes web sources with javascript support
- 📂 Keeps track and context of visited and used web sources
- 📄 Export research reports to PDF, Word and more...

## 📖 Documentation

Please see [here](https://docs.tavily.com/docs/gpt-researcher/getting-started) for full documentation on:

- Getting started (installation, setting up the environment, simple examples)
- Customization and configuration
- How-To examples (demos, integrations, docker support)
- Reference (full API docs)

## ⚙️ Getting Started
### Installation
> **Step 0** - Install Python 3.11 or later. [See here](https://www.tutorialsteacher.com/python/install-python) for a step-by-step guide.

> **Step 1** - Download the project and navigate to its directory

```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

> **Step 3** - Set up API keys using two methods: exporting them directly or storing them in a `.env` file.

For Linux/Windows temporary setup, use the export method:

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
export TAVILY_API_KEY={Your Tavily API Key here}
```

For a more permanent setup, create a `.env` file in the current `gpt-researcher` directory and input the keys as follows:

```bash
OPENAI_API_KEY={Your OpenAI API Key here}
TAVILY_API_KEY={Your Tavily API Key here}
```

- **For LLM, we recommend [OpenAI GPT](https://platform.openai.com/docs/guides/gpt)**, but you can use any other LLM model (including open sources) supported by [Langchain Adapter](https://python.langchain.com/docs/integrations/adapters/openai/), simply change the llm model and provider in config/config.py. 
- **For web search API, we recommend [Tavily Search API](https://app.tavily.com)**, but you can also refer to other search APIs of your choice by changing the search provider in config/config.py to `"duckduckgo"`, `"googleAPI"`, `"bing"`, `"googleSerp"`, `"searx"` and more. Then add the corresponding env API key as seen in the config.py file.

### Quickstart

> **Step 1** - Install dependencies

```bash
pip install -r requirements.txt
```

> **Step 2** - Run the agent with FastAPI

```bash
uvicorn main:app --reload
```

> **Step 3** - Go to http://localhost:8000 on any browser and enjoy researching!

<br />

**To learn how to get started with [Docker](https://docs.tavily.com/docs/gpt-researcher/getting-started#try-it-with-docker), [Poetry](https://docs.tavily.com/docs/gpt-researcher/getting-started#poetry) or a [virtual environment](https://docs.tavily.com/docs/gpt-researcher/getting-started#virtual-environment) check out the [documentation](https://docs.tavily.com/docs/gpt-researcher/getting-started) page.**

### Run as PIP package
```bash
pip install gpt-researcher
```

```python
from gpt_researcher import GPTResearcher

query = "why is Nvidia stock going up?"
researcher = GPTResearcher(query=query, report_type="research_report")
# Conduct research on the given query
await researcher.conduct_research()
# Write the report
report = await researcher.write_report()
```

**For more examples and configurations, please refer to the [PIP documentation](https://docs.tavily.com/docs/gpt-researcher/pip-package) page.**


## 🚀 Contributing
We highly welcome contributions! Please check out [contributing](CONTRIBUTING.md) if you're interested.

Please check out our [roadmap](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) page and reach out to us via our [Discord community](https://discord.gg/2pFkc83fRq) if you're interested in joining our mission.

## ✉️ Support / Contact us
- [Community Discord](https://discord.gg/spBgZmm3Xe)
- Our email: assafelovic@gmail.com

## 🛡 Disclaimer

This project, GPT Researcher, is an experimental application and is provided "as-is" without any warranty, express or implied. We are sharing codes for academic purposes under the MIT license. Nothing herein is academic advice, and NOT a recommendation to use in academic or research papers.

Our view on unbiased research claims:
1. The main goal of GPT Researcher is to reduce incorrect and biased facts. How? We assume that the more sites we scrape the less chances of incorrect data. By scraping over 20 sites per research, and choosing the most frequent information, the chances that they are all wrong is extremely low.
2. We do not aim to eliminate biases; we aim to reduce it as much as possible. **We are here as a community to figure out the most effective human/llm interactions.**
3. In research, people also tend towards biases as most have already opinions on the topics they research about. This tool scrapes many opinions and will evenly explain diverse views that a biased person would never have read.

**Please note that the use of the GPT-4 language model can be expensive due to its token usage.** By utilizing this project, you acknowledge that you are responsible for monitoring and managing your own token usage and the associated costs. It is highly recommended to check your OpenAI API usage regularly and set up any necessary limits or alerts to prevent unexpected charges.

---

<p align="center">
<a href="https://star-history.com/#assafelovic/gpt-researcher">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
  </picture>
</a>
</p>
