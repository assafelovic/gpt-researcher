<div align="center" id="top">
<!--<h1 style="display: flex; align-items: center; gap: 10px;">
  <img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/a45bac7c-092c-42e5-8eb6-69acbf20dde5" alt="Logo" width="25">
  GPT Researcher
</h1>-->
<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">


####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge&theme=clean-inverted&?compact=true)](https://discord.gg/QgZXvJAccX)

[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)

[English](README.md) |
[中文](README-zh_CN.md) |
[日本語](README-ja_JP.md) |
[한국어](README-ko_KR.md)
</div>

# 🔎 GPT Researcher

**GPT Researcher is an autonomous agent designed for comprehensive web and local research on any given task.** 

The agent can produce detailed, factual and unbiased research reports, with customization options for focusing on relevant resources and outlines. Inspired by the recent [Plan-and-Solve](https://arxiv.org/abs/2305.04091) and [RAG](https://arxiv.org/abs/2005.11401) papers, GPT Researcher addresses issues of misinformation, speed, determinism and reliability, offering a more stable performance and increased speed through parallelized agent work, as opposed to synchronous operations.

**Our mission is to empower individuals and organizations with accurate, unbiased, and factual information by leveraging the power of AI.** 

## Why GPT Researcher?

- Forming objective conclusions for manual research tasks can take time, sometimes weeks, to find the right resources and information
- Current LLMs are trained on past and outdated information, with heavy risks of hallucinations, making them almost irrelevant for research tasks.
- Current LLMs are limited to short token outputs, which are insufficient for long, detailed research reports (over 2,000 words).
- Services that enable web searches, such as ChatGPT or Perplexity, only consider limited sources and content, which in some cases results in misinformation and shallow results.
- Using only a selection of web sources can create bias in determining the right conclusions for research tasks.

## Demo
https://github.com/user-attachments/assets/092e9e71-7e27-475d-8c4f-9dddd28934a3

## Architecture
The main idea is to run 'planner' and 'execution' agents, where the planner generates questions for research, and the execution agents seek the most relevant information based on each generated research question. Finally, the planner filters and aggregates all related information and creates a research report. <br /> <br /> 
The agents leverage both `gpt-4o-mini` and `gpt-4o` (128K context) to complete a research task. We optimize for costs using each only when necessary. **The average research task takes about 2 minutes to complete and costs approximately $0.005.**

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527">
</div>



More specifically:
* Create a domain specific agent based on research query or task.
* Generate a set of research questions that together form an objective opinion on any given task. 
* For each research question, trigger a crawler agent that scrapes online resources for information relevant to the given task.
* For each scraped resources, summarize based on relevant information and keep track of its sources.
* Finally, filter and aggregate all summarized sources and generate a final research report.

## Tutorials
 - [How it Works](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [How to Install](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [Live Demo](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## Features
- 📝 Generate research, outlines, resources and lessons reports with local documents and web sources
- 🖼️ Supports smart article image scraping and filtering
- 📜 Can generate long and detailed research reports (over 2K words)
- 🌐 Aggregates over 20 web sources per research to form objective and factual conclusions
- 🖥️ Includes both lightweight (HTML/CSS/JS) and production ready (NextJS + Tailwind) UX/UI
- 🔍 Scrapes web sources with javascript support
- 📂 Keeps track and context and memory throughout the research process
- 📄 Export research reports to PDF, Word and more...

## 📖 Documentation

Please see [here](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started) for full documentation on:

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

For a more permanent setup, create a `.env` file in the current `gpt-researcher` directory and input the env vars (without `export`).

- The default LLM is [GPT](https://platform.openai.com/docs/guides/gpt), but you can use other LLMs such as `claude`, `ollama3`, `gemini`, `mistral` and more. To learn how to change the LLM provider, see the [LLMs documentation](https://docs.gptr.dev/docs/gpt-researcher/llms/llms) page. Please note: this project is optimized for OpenAI GPT models.
- The default retriever is [Tavily](https://app.tavily.com), but you can refer to other retrievers such as `duckduckgo`, `google`, `bing`, `searchapi`, `serper`, `searx`, `arxiv`, `exa` and more. To learn how to change the search provider, see the [retrievers documentation](https://docs.gptr.dev/docs/gpt-researcher/search-engines/retrievers) page.

### Quickstart

> **Step 1** - Install dependencies

```bash
pip install -r requirements.txt
```

> **Step 2** - Run the agent with FastAPI

```bash
python -m uvicorn main:app --reload
```

> **Step 3** - Go to http://localhost:8000 on any browser and enjoy researching!

<br />

**To learn how to get started with [Poetry](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started#poetry) or a [virtual environment](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started#virtual-environment) check out the [documentation](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started) page.**

### Run as PIP package
```bash
pip install gpt-researcher
```

```python
...
from gpt_researcher import GPTResearcher

query = "why is Nvidia stock going up?"
researcher = GPTResearcher(query=query, report_type="research_report")
# Conduct research on the given query
research_result = await researcher.conduct_research()
# Write the report
report = await researcher.write_report()
...
```

**For more examples and configurations, please refer to the [PIP documentation](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package) page.**


## Run with Docker

> **Step 1** - [Install Docker](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **Step 2** - Clone the '.env.example' file, add your API Keys to the cloned file and save the file as '.env'

> **Step 3** - Within the docker-compose file comment out services that you don't want to run with Docker.

```bash
docker-compose up --build
```

If that doesn't work, try running it without the dash:
```bash
docker compose up --build
```


> **Step 4** - By default, if you haven't uncommented anything in your docker-compose file, this flow will start 2 processes:
 - the Python server running on localhost:8000<br>
 - the React app running on localhost:3000<br>

Visit localhost:3000 on any browser and enjoy researching!



## 📄 Research on Local Documents

You can instruct the GPT Researcher to run research tasks based on your local documents. Currently supported file formats are: PDF, plain text, CSV, Excel, Markdown, PowerPoint, and Word documents.

Step 1: Add the env variable `DOC_PATH` pointing to the folder where your documents are located.

```bash
export DOC_PATH="./my-docs"
```

Step 2: 
 - If you're running the frontend app on localhost:8000, simply select "My Documents" from the "Report Source" Dropdown Options.
 - If you're running GPT Researcher with the [PIP package](https://docs.tavily.com/docs/gpt-researcher/pip-package), pass the `report_source` argument as "local" when you instantiate the `GPTResearcher` class [code sample here](https://docs.gptr.dev/docs/gpt-researcher/context/tailored-research).


## 👪 Multi-Agent Assistant
As AI evolves from prompt engineering and RAG to multi-agent systems, we're excited to introduce our new multi-agent assistant built with [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/).

By using LangGraph, the research process can be significantly improved in depth and quality by leveraging multiple agents with specialized skills. Inspired by the recent [STORM](https://arxiv.org/abs/2402.14207) paper, this project showcases how a team of AI agents can work together to conduct research on a given topic, from planning to publication.

An average run generates a 5-6 page research report in multiple formats such as PDF, Docx and Markdown.

Check it out [here](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents) or head over to our [documentation](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph) for more information.

## 🖥️ Frontend Applications

GPT-Researcher now features an enhanced frontend to improve the user experience and streamline the research process. The frontend offers:

- An intuitive interface for inputting research queries
- Real-time progress tracking of research tasks
- Interactive display of research findings
- Customizable settings for tailored research experiences

Two deployment options are available:
1. A lightweight static frontend served by FastAPI
2. A feature-rich NextJS application for advanced functionality

For detailed setup instructions and more information about the frontend features, please visit our [documentation page](https://docs.gptr.dev/docs/gpt-researcher/frontend/frontend).

## 🚀 Contributing
We highly welcome contributions! Please check out [contributing](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md) if you're interested.

Please check out our [roadmap](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) page and reach out to us via our [Discord community](https://discord.gg/QgZXvJAccX) if you're interested in joining our mission.
<a href="https://github.com/assafelovic/gpt-researcher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=assafelovic/gpt-researcher" />
</a>
## ✉️ Support / Contact us
- [Community Discord](https://discord.gg/spBgZmm3Xe)
- Author Email: assaf.elovic@gmail.com

## 🛡 Disclaimer

This project, GPT Researcher, is an experimental application and is provided "as-is" without any warranty, express or implied. We are sharing codes for academic purposes under the Apache 2 license. Nothing herein is academic advice, and NOT a recommendation to use in academic or research papers.

Our view on unbiased research claims:
1. The main goal of GPT Researcher is to reduce incorrect and biased facts. How? We assume that the more sites we scrape the less chances of incorrect data. By scraping multiple sites per research, and choosing the most frequent information, the chances that they are all wrong is extremely low.
2. We do not aim to eliminate biases; we aim to reduce it as much as possible. **We are here as a community to figure out the most effective human/llm interactions.**
3. In research, people also tend towards biases as most have already opinions on the topics they research about. This tool scrapes many opinions and will evenly explain diverse views that a biased person would never have read.

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


<p align="right">
  <a href="#top">⬆️ Back to Top</a>
</p>
