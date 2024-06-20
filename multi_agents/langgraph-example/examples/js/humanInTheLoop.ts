import { Client } from "@langchain/langgraph-sdk";

async function main() {
  const client = new Client();

  const assistant = await client.assistants.create({ graphId: "agent" });
  console.log("Assistant", assistant);

  // Approve a tool call
  const thread = await client.threads.create();
  console.log("Thread", thread);

  let runs = await client.runs.list(thread.thread_id);
  console.log("Runs", runs);

  // We now want to add a human-in-the-loop step before a tool is called.
  // We can do this by adding `interruptBefore=["action"]`, which tells us to interrupt before calling the action node.
  // We can do this either when compiling the graph or when kicking off a run.
  // Here we will do it when kicking of a run.
  let input = {
    messages: [{ role: "human", content: "whats the weather in sf" }],
  };
  for await (const chunk of client.runs.stream(
    thread.thread_id,
    assistant.assistant_id,
    {
      input,
      streamMode: "updates",
      interruptBefore: ["action"],
    }
  )) {
    console.log(`Receiving new event of type: ${chunk.event}...`);
    console.log(JSON.stringify(chunk.data));
    console.log("\n\n");
  }

  // We can now kick off a new run on the same thread with `None` as the input in order to just continue the existing thread.
  for await (const chunk of client.runs.stream(
    thread.thread_id,
    assistant.assistant_id,
    {
      input: null,
      streamMode: "updates",
      interruptBefore: ["action"],
    }
  )) {
    console.log(`Receiving new event of type: ${chunk.event}...`);
    console.log(JSON.stringify(chunk.data));
    console.log("\n\n");
  }

  // Edit a tool call

  // What if we want to edit the tool call?
  // We can also do that.
  // Let's kick off another run, with the same `interruptBefore=['action']`
  input = {
    messages: [{ role: "human", content: "whats the weather in la?" }],
  };
  for await (const chunk of client.runs.stream(
    thread.thread_id,
    assistant.assistant_id,
    {
      input: input,
      streamMode: "updates",
      interruptBefore: ["action"],
    }
  )) {
    console.log(`Receiving new event of type: ${chunk.event}...`);
    console.log(JSON.stringify(chunk.data));
    console.log("\n\n");
  }

  // Inspect and modify the state of the thread
  let threadState = await client.threads.getState(thread.thread_id);
  // Let's get the last message of the thread - this is the one we want to update
  let lastMessage = threadState.values["messages"].slice(-1)[0];

  // Let's now modify the tool call to say Louisiana
  lastMessage.tool_calls = [
    {
      name: "tavily_search_results_json",
      args: { query: "weather in Louisiana" },
      id: lastMessage.tool_calls[0].id,
    },
  ];

  await client.threads.updateState(thread.thread_id, {
    values: { messages: [lastMessage] },
  });

  // Check the updated state
  threadState = await client.threads.getState(thread.thread_id);
  console.log(
    "Updated tool calls",
    threadState.values["messages"].slice(-1)[0].tool_calls
  );

  // Great! We changed it. If we now resume execution (by kicking off a new run with null inputs on the same thread) it should use that new tool call.
  for await (const chunk of client.runs.stream(
    thread.thread_id,
    assistant.assistant_id,
    {
      input: null,
      streamMode: "updates",
      interruptBefore: ["action"],
    }
  )) {
    console.log(`Receiving new event of type: ${chunk.event}...`);
    console.log(JSON.stringify(chunk.data));
    console.log("\n\n");
  }

  // Edit an old state

  // Let's now imagine we want to go back in time and edit the tool call after we had already made it.
  // In order to do this, we can get first get the full history of the thread
  const threadHistory = await client.threads.getHistory(thread.thread_id, {
    limit: 100,
  });
  console.log("History length", threadHistory.length);

  // After that, we can get the correct state we want to be in. The 0th index state is the most recent one, while the -1 index state is the first.
  // In this case, we want to go to the state where the last message had the tool calls for `weather in los angeles`
  const rewindState = threadHistory[3];
  console.log(
    "Rewind state tools calls",
    rewindState.values["messages"].slice(-1)[0].tool_calls
  );

  for await (const chunk of client.runs.stream(
    thread.thread_id,
    assistant.assistant_id,
    {
      input: null,
      streamMode: "updates",
      interruptBefore: ["action"],
      config: rewindState.config,
    }
  )) {
    console.log(`Receiving new event of type: ${chunk.event}...`);
    console.log(JSON.stringify(chunk.data));
    console.log("\n\n");
  }
}

main();
