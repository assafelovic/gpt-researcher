# Agent Frameworks

We are strong advocates for the future of AI agents, envisioning a world where autonomous agents communicate and collaborate as a cohesive team to undertake and complete complex tasks.

We hold the belief that research is a pivotal element in successfully tackling these complex tasks, ensuring superior outcomes.

Consider the scenario of developing a coding agent responsible for coding tasks using the latest API documentation and best practices. It would be wise to integrate an agent specializing in research to curate the most recent and relevant documentation, before crafting a technical design that would subsequently be handed off to the coding assistant tasked with generating the code. This approach is applicable across various sectors, including finance, business analysis, healthcare, marketing, and legal, among others.

One agent framework that we're excited about is [PermChain](https://github.com/langchain-ai/permchain), built by the amazing team at [Langchain](https://www.langchain.com/).
PermChain is a Python library for building stateful, multi-actor applications with LLMs. It extends the [LangChain Expression Language](https://python.langchain.com/docs/expression_language/) with the ability to coordinate multiple chains (or actors) across multiple steps of computation.

What's great about PermChain is that it follows an event driven architecture, enabling each agent to both subscribe to and publish topics, which can subsequently trigger actions among other agents within the chain. 

We've added an example for leveraging [GPT Researcher with PermChain](https://github.com/assafelovic/gpt-researcher/tree/master/examples/permchain_agents) which can be found in `/example/permchain_agents/`.

The example demonstrates a generic use case for an editorial agent team that works together to complete a research report on a given task.

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
   
The agent team can be easily extended to business use cases such as generating marketing campaigns based on a specific report, or generating code based on collected documentation.

We're working on supporting more and more agent framework examples which can be found in `/examples/`