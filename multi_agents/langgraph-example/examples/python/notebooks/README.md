# How-to guides

These are how-to guides for interacting with the deployed agents.


## Streaming

When you deploy a graph with LangGraph API, you can stream results from a run in a few different ways.

- `values`: This streaming mode streams back values of the graph. This is the **full state of the graph** after each node is called.
- `update`: This streaming mode streams back updates to the graph. This is the **update to the state of the graph** after each node is called.
- `messages`: This streaming mode streams back messages - both complete messages (at the end of a node) as well as **tokens** for any messages generated inside a node. This mode is primarily meant for powering chat applications.

See the following guides for how to use the different streaming modes.


- [How to stream values](./stream_values.ipynb)
- [How to stream updates](./stream_updates.ipynb)
- [How to stream messages](./stream_messages.ipynb)

## Background runs

When you deploy a graph with LangGraph API, you can also interact with it in a way where you kick off background runs.
You can poll for the status of the run.
This can be useful when the run is particularly long running.

- [How to kick off a background run](./background_run.ipynb)

## Human-in-the-loop

When you deploy a graph with LangGraph API, it is deployed with a persistence layer.
This enables easy human-in-the-loop interactions like approving a tool call, editing a tool call, and returning to and modifying a previous state and resuming execution from there.

- [How to have a human in the loop](./human-in-the-loop.ipynb)

## Configuration

One of the benefits of LangGraph API is that it lets you create agents with different configurations.
This is useful when you want to:

1. Define a cognitive architecture once as a LangGraph
2. Let that LangGraph be configurable across some attributes (for example, system message or LLM to use)
3. Let users create agents with arbitrary configurations, save them, and then use them in the future

In this guide we will show how to do that for the default agent we have built in.

- [How to configure agents](./configuration.ipynb)

## Multiple Agents, Same Thread

In LangGraph API, a thread is not explicitly associated with a particular agent.
This means that you can run multiple agents on the same thread.
In this example, we will create two agents and then call them both on the same thread.

- [How to run multiple agents on the same thread](./same-thread.ipynb)