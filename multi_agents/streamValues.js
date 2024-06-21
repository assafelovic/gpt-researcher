import { Client } from "@langchain/langgraph-sdk";

async function streamValues() {
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
    { input }
  )) {
    console.log(`Receiving new event of type: ${event.event}...`);
    console.log(JSON.stringify(event.data));
    console.log("\n\n");
  }

  // List all assistants
  const assistants = await client.assistants.search({
    metadata: null,
    offset: 0,
    limit: 10,
  });

  console.log('assistants: ',assistants);
}

streamValues();