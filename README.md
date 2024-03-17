# 🔎 GPT Researcher
[![Official Website](https://img.shields.io/badge/Official%20Website-tavily.com-blue?style=for-the-badge&logo=world&logoColor=white)](https://tavily.com)
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
- Solutions that enable web search (such as ChatGPT + Web Plugin), only consider limited resources and content that in some cases result in superficial conclusions or biased answers.
- Using only a selection of resources can create bias in determining the right conclusions for research questions or tasks. 

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

## Demo
https://github.com/assafelovic/gpt-researcher/assets/13554167/a00c89a6-a295-4dd0-b58d-098a31c40fda

## Tutorials
 - [How it Works](https://docs.tavily.com/blog/building-gpt-researcher)
 - [How to Install](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [Live Demo](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## Features
- 📝 Generate research, outlines, resources and lessons reports
- 🌐 Aggregates over 20 web sources per research to form objective and factual conclusions
- 🖥️ Includes an easy-to-use web interface (HTML/CSS/JS)
- 🔍 Scrapes web sources with javascript support
- 📂 Keeps track and context of visited and used web sources
- 📄 Export research reports to PDF and more...

## 📖 Documentation

Please see [here](https://docs.tavily.com/docs/gpt-researcher/getting-started) for full documentation on:

- Getting started (installation, setting up the environment, simple examples)
- How-To examples (demos, integrations, docker support)
- Reference (full API docs)
- Tavily API integration (high-level explanation of core concepts)

## Quickstart
> **Step 0** - Install Python 3.11 or later. [See here](https://www.tutorialsteacher.com/python/install-python) for a step-by-step guide.

<br />

> **Step 1** - Download the project and navigate to its directory. You'll encounter two options: Virtual Environment and Poetry. Select either Step-2 or Step-3 based on your familiarity with each.:

```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

<br />

> **Step 2** - 🌐🌀 Virtual Environment 🛡️.

#### *Establishing the Virtual Environment with Activate/Deactivate configuration*

Create a virtual environment using the `venv` package with the environment name `<your_name>`, for example, `env`. Execute the following command in the PowerShell/CMD terminal:

```bash
python -m venv env
```

To activate the virtual environment, use the following activation script in PowerShell/CMD terminal:

```bash
.\env\Scripts\activate
```

To deactivate the virtual environment, run the following deactivation script in PowerShell/CMD terminal:

```bash
deactivate
```

#### *Install the dependencies for a Virtual environment*

After activating the `env` environment, install dependencies using the `requirements.txt` file with the following command:

```bash
python -m pip install -r requirements.txt
```

<br />

> **Step 3** - 📜🎭 Poetry 📝

#### *Establishing the Poetry dependencies and virtual environment with Poetry version `~1.7.1`*

Install project dependencies and simultaneously create a virtual environment for the specified project. By executing this command, Poetry reads the project's "pyproject.toml" file to determine the required dependencies and their versions, ensuring a consistent and isolated development environment. The virtual environment allows for a clean separation of project-specific dependencies, preventing conflicts with system-wide packages and enabling more straightforward dependency management throughout the project's lifecycle.

```bash
poetry install
```

#### *Activate the virtual environment associated with a Poetry project*

By running this command, the user enters a shell session within the isolated environment associated with the project, providing a dedicated space for development and execution. This virtual environment ensures that the project dependencies are encapsulated, avoiding conflicts with system-wide packages. Activating the Poetry shell is essential for seamlessly working on a project, as it ensures that the correct versions of dependencies are used and provides a controlled environment conducive to efficient development and testing.

```bash
poetry shell
```

<br />

> **Step 4** - Set up API keys using two methods: exporting them directly and storing them in a `.env` file.

For Linux/Temporary Windows Setup, use the export method:

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
export TAVILY_API_KEY={Your Tavily API Key here}
```

For a more permanent setup, create a `.env` file in the current `gpt-researcher` folder and input the keys as follows:

```bash
OPENAI_API_KEY={Your OpenAI API Key here}
TAVILY_API_KEY={Your Tavily API Key here}
```

- **For LLM, we recommend [OpenAI GPT](https://platform.openai.com/docs/guides/gpt)**, but you can use any other LLM model (including open sources) supported by [Langchain Adapter](https://python.langchain.com/docs/guides/adapters/openai), simply change the llm model and provider in config/config.py. Follow [this guide](https://python.langchain.com/docs/integrations/llms/) to learn how to integrate LLMs with Langchain. 
- **For search engine, we recommend [Tavily Search API](https://app.tavily.com) (optimized for LLMs)**, but you can also refer to other search engines of your choice by changing the search provider in config/config.py to `"duckduckgo"`, `"googleAPI"`, `"googleSerp"`, or `"searx"`. Then add the corresponding env API key as seen in the config.py file.
- **We highly recommend using [OpenAI GPT](https://platform.openai.com/docs/guides/gpt) models and [Tavily Search API](https://app.tavily.com) for optimal performance.**

<br />

> **Step 5** - Launch the FastAPI application agent on a *Virtual Environment or Poetry* setup by executing the following command:
```bash
python -m uvicorn main:app --reload
```

- **Issue: OSError** - For Windows 11 Pro/Home users encountering the 'OSError: cannot load library 'gobject-2.0-0'' error, please refer to [this OSError GitHub issue](https://github.com/assafelovic/gpt-researcher/issues/314). To resolve this issue, install the `WeasyPrint` software on your local machine by using the [GTK for Windows Runtime Environment Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/tag/2022-01-04).

<br />

> **Step 6** - Visit http://localhost:8000 in any web browser and explore your research!

To learn how to get started with Docker or to learn more about the features and services check out the [documentation](https://docs.tavily.com) page.

## 🚀 Contributing
We highly welcome contributions! Please check out [contributing](CONTRIBUTING.md) if you're interested.

Please check out our [roadmap](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) page and reach out to us via our [Discord community](https://discord.gg/2pFkc83fRq) if you're interested in joining our mission.

## 🛡 Disclaimer

This project, GPT Researcher, is an experimental application and is provided "as-is" without any warranty, express or implied. We are sharing codes for academic purposes under the MIT license. Nothing herein is academic advice, and NOT a recommendation to use in academic or research papers.

Our view on unbiased research claims:
1. The whole point of our scraping system is to reduce incorrect fact. How? The more sites we scrape the less chances of incorrect data. We are scraping 20 per research, the chances that they are all wrong is extremely low.
2. We do not aim to eliminate biases; we aim to reduce it as much as possible. **We are here as a community to figure out the most effective human/llm interactions.**
3. In research, people also tend towards biases as most have already opinions on the topics they research about. This tool scrapes many opinions and will evenly explain diverse views that a biased person would never have read.

**Please note that the use of the GPT-4 language model can be expensive due to its token usage.** By utilizing this project, you acknowledge that you are responsible for monitoring and managing your own token usage and the associated costs. It is highly recommended to check your OpenAI API usage regularly and set up any necessary limits or alerts to prevent unexpected charges.

## ✉️ Support / Contact us
- [Community Discord](https://discord.gg/spBgZmm3Xe)
- Our email: assafelovic@gmail.com
