# ResearchGPT
ResearchGPT is an open-source autonomous agent designed for comprehensive online research on a variety of tasks. It produces detailed research reports in PDF format, with customization options for focusing on relevant resources, outlines, and lessons. Inspired by AutoGPT, ResearchGPT addresses issues of speed and determinism, offering a more stable performance and increased speed through parallelized agent work, as opposed to synchronous operation.

# Why ResearchGPT?

- To form abjective conclusions for manual research tasks can take time, sometimes weeks to find the right online resources.
- Current LLMs are trained on past and sometimes irrelevant information.
- Solutions that enable web search such as ChatGPT + Web Plugin, only consider limited resources that in some cases result in superficial conclusions or biased answers.
- Using only a selection of resources can create bias in determing the right conclusions and answers. 

# Architecture
The main idea is to run a "planner" and "execution" agent, whereas the planner generates questions to research, and the execution agents seek the most related information. Finally, the planner aggregates all related information and creates a final research report.

<div align="center">
<img align="center" height="500" src="https://cowriter-images.s3.amazonaws.com/architecture.png">
</div>

More specifcally:
* Generate a set of research questions that together form an objective opinion on any task. 
* For each research question, trigger a research agent that scrapes online resources for information relevant to the given task.
* For each relevant inforamtion, summarize it and keep track of its sources.
* Finally, aggreate all summarized information and generate a final research report.

<h2 align="center"> Demo </h2>

## Quickstart

> **Step #1** - Download the project

```bash
$ git clone https://github.com/assafelovic/researchGPT.git
$ cd researchGPT
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

> **Step #4** - Run the agent and enjoy researching!

```bash
$ python main.py
```

## 🛡 Disclaimer

This project, ResearchGPT, is an experimental application and is provided "as-is" without any warranty, express or implied. We are sharing codes for academic purposes under the MIT education license. Nothing herein is academic advice, and NOT a recommendation to use in academic or research papers.

**Please note that the use of the GPT-4 language model can be expensive due to its token usage.** By utilizing this project, you acknowledge that you are responsible for monitoring and managing your own token usage and the associated costs. It is highly recommended to check your OpenAI API usage regularly and set up any necessary limits or alerts to prevent unexpected charges.
