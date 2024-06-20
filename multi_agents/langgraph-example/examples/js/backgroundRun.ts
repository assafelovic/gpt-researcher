// How to kick off background runs
// This guide covers how to kick off background runs for your agent. This can be useful for long running jobs.
import { Client } from "@langchain/langgraph-sdk";

async function main() {
  // Initialize the client
  const client = new Client();

  // List available assistants
  const assistants = await client.assistants.search();
  console.log("List available assistants", assistants);

  // Get the first assistant, we will use this one
  const assistant = assistants[0];
  console.log("Get first assistant", assistant);

  // Create a new thread
  const thread = await client.threads.create();
  console.log("Create new thread", thread);

  // If we list runs on this thread, we can see it is empty
  const runs = await client.runs.list(thread.thread_id);
  console.log("List runs on the thread", runs);

  // Let's kick off a run
  const input = {
    messages: [{ role: "human", content: "whats the weather in sf" }],
  };
  const run = await client.runs.create(
    thread.thread_id,
    assistant.assistant_id,
    { input }
  );
  console.log("Create a single run", run);

  // The first time we poll it, we can see `status=pending`
  console.log(
    "Poll a single run, status=pending",
    await client.runs.get(thread.thread_id, run.run_id)
  );

  // We can list events for the run
  console.log(
    "List all events for the run",
    await client.runs.listEvents(thread.thread_id, run.run_id)
  );

  // Eventually, it should finish and we should see `status=success`
  let finalRunStatus = await client.runs.get(thread.thread_id, run.run_id);
  while (finalRunStatus.status !== "success") {
    await new Promise((resolve) => setTimeout(resolve, 1000)); // Polling every second
    finalRunStatus = await client.runs.get(thread.thread_id, run.run_id);
  }
  console.log(
    "Final run status",
    await client.runs.get(thread.thread_id, run.run_id)
  );

  // We can get the final results
  const results = await client.runs.listEvents(thread.thread_id, run.run_id);

  // The results are sorted by time, so the most recent (final) step is the 0 index
  const finalResult = results[0];
  console.log("Final result", finalResult);

  // We can get the content of the final message
  const finalMessages = (finalResult.data as Record<string, any>)["output"][
    "messages"
  ];
  const finalMessageContent = finalMessages[finalMessages.length - 1].content;
  console.log("Final message content", finalMessageContent);
}

main();
