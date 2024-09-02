# LangGraph

[LangGraph](https://python.langchain.com/docs/langgraph) is a library for building stateful, multi-actor applications with LLMs. 

Within the GPT-Reasearcher project, LangGraph is used to orchestrate the multi-agent flow of both a Research Team and a Development Team.

You can think of LangGraph as a way to manage the flow of information between different agents, each with their own specialized skills.

It's kind of like what middleware backend functions, but for AI agents.

Each agent can have a variety of methods that takes in some input and returns some output. LangGraph manages the flow of information between these agents, allowing them to work together to accomplish a common goal.
