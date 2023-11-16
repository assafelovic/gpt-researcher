# Getting Started
## Quickstart
> **Step 0** - Install Python 3.11 or later. [See here](https://www.tutorialsteacher.com/python/install-python) for a step-by-step guide.

> **Step 1** - Download the project

```bash
$ git clone https://github.com/assafelovic/gpt-researcher.git
$ cd gpt-researcher
```

> **Step 2** - Install dependencies

```bash
$ pip install -r requirements.txt
```

> **Step 3** - Create .env file with your OpenAI Key and Tavily API key or simply export it

```bash
$ export OPENAI_API_KEY={Your OpenAI API Key here}
```
```bash
$ export TAVILY_API_KEY={Your Tavily API Key here}
```

- **For LLM, we recommend [OpenAI GPT](https://platform.openai.com/docs/guides/gpt)**, but you can use any other LLM model (including open sources) supported by [Langchain Adapter](https://python.langchain.com/docs/guides/adapters/openai), simply change the llm model and provider in config/config.py. Follow [this guide](https://python.langchain.com/docs/integrations/llms/) to learn how to integrate LLMs with Langchain. 
- **For search engine, we recommend [Tavily Search API](https://app.tavily.com) (optimized for LLMs)**, but you can also refer to other search engines of your choice by changing the search provider in config/config.py to `"duckduckgo"`, `"googleAPI"`, `"googleSerp"`, or `"searx"`. Then add the corresponding env API key as seen in the config.py file.
- **We highly recommend using [OpenAI GPT](https://platform.openai.com/docs/guides/gpt) models and [Tavily Search API](https://app.tavily.com) for optimal performance.**

> **Step 4** - Run the agent with FastAPI

```bash
$ uvicorn main:app --reload
```

> **Step 5** - Go to http://localhost:8000 on any browser and enjoy researching!

## Try it with Docker

> **Step 1** - Install Docker

Follow instructions at https://docs.docker.com/engine/install/

> **Step 2** - Create .env file with your OpenAI Key or simply export it

```bash
$ export OPENAI_API_KEY={Your API Key here}
$ export TAVILY_API_KEY={Your Tavily API Key here}
```

> **Step 3** - Run the application

```bash
$ docker-compose up
```

> **Step 4** - Go to http://localhost:8000 on any browser and enjoy researching!

## Try it with PIP Pacakge
