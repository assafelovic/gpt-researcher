# Langgraph x GPT Researcher
Example of Langchain's multi agent framework Langgraph with GPT Researcher.

## Use case
LangGraph is a library for building stateful, multi-actor applications with LLMs, built on top of LangChain. 
This example uses Langgraph to automate the process of an in depth research on any given topic.

## The Multi Agent Team
The research team is made up of 7 AI agents:
- *Chief Editor* - Oversees the research process and manages the team. This is the "master" agent that coordinates the other agents using Langgraph.
- *Researcher* (gpt-researcher) - A specialized autonomous agent that conducts in depth research on a given topic.
- *Editor* - Responsible for planning the research outline and structure.
- *Reviewer* - Validates the correctness of the research results given a set of criteria.
- *Revisor* - Revises the research results based on the feedback from the reviewer.
- *Writer* - Responsible for compiling and writing the final report.
- *Publisher* - Responsible for publishing the final report in various formats.

## How it works
Generally, the process is based on the following stages: 
1. Planning stage
2. Data collection and analysis
3. Writing and submission
4. Review and revision
5. Publication

[Image](https://google.com)

More specifically (as seen in the architecture diagram) the process is as follows:
- Browser (gpt-researcher) - Browses the internet for initial research based on the given research task.
- Editor - Plans the report outline and structure based on the initial research.
- Below runs in parallel for each section of the planned research outline:
  - Researcher (gpt-researcher) - Runs an in depth research on the subtopic and writes a draft.
  - Reviewer - Validates the correctness of the draft given a set of criteria.
  - Revisor - Revises the draft until it is satisfactory.
- Writer - Compiles and writes the final report including an introduction, conclusion and references section from the given research findings.
- Publisher - Publishes the final report to multi formats such as PDF, Docx, Markdown, etc.

## How to run
1. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```
2. Run the application:
    ```bash
    python main.py
    ```

## Usage
To change the research topic and customize the report, edit the `task.json` file in the main directory.