# 🔎 GPT Researcher
GPT Researcher is an autonomous agent designed for comprehensive online research on a variety of tasks. It produces detailed, factual and unbiased research reports, with customization options for focusing on relevant resources, outlines, and lessons. Inspired by [AutoGPT](https://github.com/Significant-Gravitas/Auto-GPT) and the recent [Plan-and-Solve](https://arxiv.org/abs/2305.04091) paper, GPT Researcher addresses issues of speed and determinism, offering a more stable performance and increased speed through parallelized agent work, as opposed to synchronous operations.

Our mission is to empower individuals and organizations with accurate, unbiased, and factual information by leveraging the power of AI.

# Why GPT Researcher?

- To form objective conclusions for manual research tasks can take time, sometimes weeks to find the right resources and information.
- Current LLMs are trained on past and outdated information, with heavy risks of hallucinations, making them almost irrelevant for research tasks.
- Solutions that enable web search (such as ChatGPT + Web Plugin), only consider limited resources that in some cases result in superficial conclusions or biased answers.
- Using only a selection of resources can create bias in determing the right conclusions for research questions or tasks. 

# Architecture
The main idea is to run "planner" and "execution" agents, whereas the planner generates questions to research, and the execution agents seek the most related information based on each generated research question. Finally, the planner filters and aggregates all related information and creates a research report. The agents leverage both gpt3.5-turbo-16k and gpt-4 to complete a research task.

<div align="center">
<img align="center" height="500" src="https://cowriter-images.s3.amazonaws.com/arch.png">
</div>


More specifcally:
* Generate a set of research questions that together form an objective opinion on any given task. 
* For each research question, trigger a crawler agent that scrapes online resources for information relevant to the given task.
* For each scraped resources, summarize based on relevant information and keep track of its sources.
* Finally, filter and aggregate all summarized sources and generate a final research report.

# Demo
https://github.com/assafelovic/gpt-researcher/assets/13554167/a00c89a6-a295-4dd0-b58d-098a31c40fda

# Quickstart

> **Step #1** - Download the project

```bash
$ git clone https://github.com/assafelovic/researchGPT.git
$ cd gpt-researcher
```

<br />

> **Step #2** - Install dependencies
```bash
$ pip install -r requirements.txt
```
<br />

> **Step #3** - Create .env file with your OpenAI Key or simply export it

```bash
$ export OPENAI_API_KEY={Your API Key here}
```
<br />

> **Step #4** - Run the agent with FastAPI

```bash
$ uvicorn main:app --reload
```
<br />

> **Step #5** - Go to http://localhost:8000 on any browser and enjoy researching!

## 🛡 Disclaimer

This project, GPT Researcher, is an experimental application and is provided "as-is" without any warranty, express or implied. We are sharing codes for academic purposes under the MIT education license. Nothing herein is academic advice, and NOT a recommendation to use in academic or research papers.

**Please note that the use of the GPT-4 language model can be expensive due to its token usage.** By utilizing this project, you acknowledge that you are responsible for monitoring and managing your own token usage and the associated costs. It is highly recommended to check your OpenAI API usage regularly and set up any necessary limits or alerts to prevent unexpected charges.
