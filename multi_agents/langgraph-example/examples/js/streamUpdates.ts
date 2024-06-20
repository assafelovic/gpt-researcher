// How to stream updates from your graph
import { Client } from "@langchain/langgraph-sdk";

/*
There are multiple different streaming modes.

- values: This streaming mode streams back values of the graph. This is the full state of the graph after each node is called.
- updates: This streaming mode streams back updates to the graph. This is the update to the state of the graph after each node is called.
- messages: This streaming mode streams back messages - both complete messages (at the end of a node) as well as tokens for any messages generated inside a node. This mode is primarily meant for powering chat applications.

This script covers streaming_mode="updates".
*/

async function streamUpdates() {
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

  const input = {
    messages: [{ role: "user", content: "whats the weather in sf" }],
  };

  for await (const event of client.runs.stream(
    thread.thread_id,
    assistant.assistant_id,
    { input, streamMode: "updates" }
  )) {
    console.log(`Receiving new event of type: ${event.event}...`);
    console.log(JSON.stringify(event.data));
    console.log("\n\n");
  }
}

streamUpdates();
