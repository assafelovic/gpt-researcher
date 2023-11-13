# Permchain x Researcher
Sample use of Langchain's Autonomous agent framework Permchain with GPT Researcher.

## Use case
Permchain is a framework for building autonomous agents that can be used to automate tasks and communication between agents to complete complex tasks. This example uses Permchain to automate the process of finding and summarizing research reports on any given topic.

## The Agent Team
The research team is made up of 3 agents:
- Researcher agent (gpt-researcher) - This agent is in charge of finding and summarizing relevant research papers.
- Editor agent - This agent is in charge of validating the correctness of the report given a set of criteria.
- Reviser agent - This agent is in charge of revising the report until it is satisfactory.

## How it works
The research agent (gpt-researcher) is in charge of finding and summarizing relevant research papers. It does this by using the following process:
- Search for relevant research papers using a search engine
- Extract the relevant information from the research papers
- Summarize the information into a report
- Send the report to the editor agent for validation
- Send the report to the reviser agent for revision
- Repeat until the report is satisfactory

## How to run
1. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```
2. Run the application:
    ```bash
    python test.py
    ```
   
## Usage
To change the research topic, edit the `query` variable in `test.py` to the desired topic.