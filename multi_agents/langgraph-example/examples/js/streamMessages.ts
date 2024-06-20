// How to stream messages from your graph
import { Client } from "@langchain/langgraph-sdk";

/*
There are multiple different streaming modes.

- values: This streaming mode streams back values of the graph. This is the full state of the graph after each node is called.
- updates: This streaming mode streams back updates to the graph. This is the update to the state of the graph after each node is called.
- messages: This streaming mode streams back messages - both complete messages (at the end of a node) as well as tokens for any messages generated inside a node. This mode is primarily meant for powering chat applications.

This script covers streaming_mode="messages".

In order to use this mode, the state of the graph you are interacting with MUST have a messages key that is a list of messages. Eg, the state should look something like:

from typing import TypedDict, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

    OR it should be an instance or subclass of from langgraph.graph import MessageState (MessageState is just a helper type hint equivalent to the above).

With stream_mode="messages" two things will be streamed back:

It outputs messages produced by any chat model called inside (unless tagged in a special way)
It outputs messages returned from nodes (to allow for nodes to return ToolMessages and the like
*/

async function streamMessages() {
  const client = new Client();
  const assistant = await client.assistants.create({
    graphId: "agent",
    config: { configurable: { model_name: "openai" } },
  });
  console.log("Assistant", assistant);

  const thread = await client.threads.create();
  console.log("Thread", thread);

  const runs = await client.runs.list(thread.thread_id);
  console.log("Runs", runs);

  // Helper function for formatting messages
  function formatToolCalls(toolCalls) {
    if (toolCalls && toolCalls.length > 0) {
      const formattedCalls = toolCalls.map(
        (call) =>
          `Tool Call ID: ${call.id}, Function: ${
            call.name
          }, Arguments: ${JSON.stringify(call.args)}`
      );
      return formattedCalls.join("\n");
    }
    return "No tool calls";
  }

  const input = {
    messages: [{ role: "user", content: "whats the weather in sf" }],
  };

  for await (const event of client.runs.stream(
    thread.thread_id,
    assistant.assistant_id,
    { input, streamMode: "messages" }
  )) {
    if (event.event === "metadata") {
      const data = event.data as Record<string, any>;
      console.log(`Metadata: Run ID - ${data["run_id"]}`);
    } else if (event.event === "messages/partial") {
      for (const dataItem of event.data as Record<string, any>[]) {
        if ("role" in dataItem && dataItem.role === "user") {
          console.log(`Human: ${dataItem.content}`);
        } else {
          const toolCalls = dataItem.tool_calls || [];
          const invalidToolCalls = dataItem.invalid_tool_calls || [];
          const content = dataItem.content || "";
          const responseMetadata = dataItem.response_metadata || {};

          if (content) {
            console.log(`AI: ${content}`);
          }

          if (toolCalls.length > 0) {
            console.log("Tool Calls:");
            console.log(formatToolCalls(toolCalls));
          }

          if (invalidToolCalls.length > 0) {
            console.log("Invalid Tool Calls:");
            console.log(formatToolCalls(invalidToolCalls));
          }

          if (responseMetadata) {
            const finishReason = responseMetadata.finish_reason || "N/A";
            console.log(`Response Metadata: Finish Reason - ${finishReason}`);
          }
        }
      }
      console.log("-".repeat(50));
    }
  }
}

streamMessages();
