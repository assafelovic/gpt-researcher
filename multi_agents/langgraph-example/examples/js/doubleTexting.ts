// How to handle "double-texting" or concurrent runs in your graph

/* 
You might want to start a new run on a thread while the previous run still haven't finished. We call this "double-texting" or multi-tasking.

There are several strategies for handling this:

- `reject`: Reject the new run.
- `interrupt`: Interrupt the current run, keeping steps completed until now, and start a new one.
- `rollback`: Cancel and delete the existing run, rolling back the thread to the state before it had started, then start the new run.
- `enqueue`: Queue up the new run to start after the current run finishes.
*/

import { Client } from "@langchain/langgraph-sdk";

const sleep = async (ms: number) =>
  await new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  const client = new Client();
  const assistant = await client.assistants.create({
    graphId: "agent",
  });

  // REJECT
  console.log("\nREJECT demo\n");
  let thread = await client.threads.create();
  let run = await client.runs.create(
    thread["thread_id"],
    assistant["assistant_id"],
    {
      input: {
        messages: [{ role: "human", content: "whats the weather in sf?" }],
      },
    },
  );

  // attempt a new run (will be rejected)
  await client.runs.create(thread["thread_id"], assistant["assistant_id"], {
    input: {
      messages: [{ role: "human", content: "whats the weather in nyc?" }],
    },
    multitaskStrategy: "reject",
  });

  await client.runs.join(thread["thread_id"], run["run_id"]);

  // We can verify that the original thread finished executing:
  let state = await client.threads.getState(thread["thread_id"]);
  console.log("Messages", state["values"]["messages"]);

  // INTERRUPT
  console.log("\nINTERRUPT demo\n");
  thread = await client.threads.create();
  const interruptedRun = await client.runs.create(
    thread["thread_id"],
    assistant["assistant_id"],
    {
      input: {
        messages: [{ role: "human", content: "whats the weather in sf?" }],
      },
    },
  );
  await sleep(2000);
  run = await client.runs.create(
    thread["thread_id"],
    assistant["assistant_id"],
    {
      input: {
        messages: [{ role: "human", content: "whats the weather in nyc?" }],
      },
      multitaskStrategy: "interrupt",
    },
  );
  await client.runs.join(thread["thread_id"], run["run_id"]);

  // We can see that the thread has partial data from the first run + data from the second run
  state = await client.threads.getState(thread["thread_id"]);
  console.log("Messages", state["values"]["messages"]);

  // Verify that the original, canceled run was interrupted
  console.log(
    "Interrupted run status",
    (await client.runs.get(thread["thread_id"], interruptedRun["run_id"]))[
      "status"
    ],
  );

  // ROLLBACK
  console.log("\nROLLBACK demo\n");
  thread = await client.threads.create();
  const rolledBackRun = await client.runs.create(
    thread["thread_id"],
    assistant["assistant_id"],
    {
      input: {
        messages: [{ role: "human", content: "whats the weather in sf?" }],
      },
    },
  );
  await sleep(2000);
  run = await client.runs.create(
    thread["thread_id"],
    assistant["assistant_id"],
    {
      input: {
        messages: [{ role: "human", content: "whats the weather in nyc?" }],
      },
      multitaskStrategy: "rollback",
    },
  );

  await client.runs.join(thread["thread_id"], run["run_id"]);

  // We can see that the thread only has data from the second run
  state = await client.threads.getState(thread["thread_id"]);
  console.log("Messages", state["values"]["messages"]);

  // Verify that the original, rolled back run was deleted
  try {
    await client.runs.get(thread["thread_id"], rolledBackRun["run_id"]);
  } catch (e) {
    console.log("Original run was deleted", e);
  }

  // ENQUEUE
  console.log("\nENQUEUE demo\n");
  thread = await client.threads.create();
  await client.runs.create(thread["thread_id"], assistant["assistant_id"], {
    input: {
      messages: [{ role: "human", content: "whats the weather in sf?" }],
      sleep: 5,
    },
  });
  await sleep(500);
  const secondRun = await client.runs.create(
    thread["thread_id"],
    assistant["assistant_id"],
    {
      input: {
        messages: [{ role: "human", content: "whats the weather in nyc?" }],
      },
      multitaskStrategy: "enqueue",
    },
  );
  await client.runs.join(thread["thread_id"], secondRun["run_id"]);

  // Verify that the thread has data from both runs
  state = await client.threads.getState(thread["thread_id"]);
  console.log("Combined messages", state["values"]["messages"]);
}

main();
