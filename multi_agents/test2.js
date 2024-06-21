import { Client } from "@langchain/langgraph-sdk";
import {task} from './config/task.js';

const client = new Client();

// List all assistants
const assistants = await client.assistants.search({
  metadata: null,
  offset: 0,
  limit: 10,
});

console.log( 'assistants',assistants);

// We auto-create an assistant for each graph you register in config.
const agent = assistants[0];

// Start a new thread
const thread = await client.threads.create();

const streamResponse = client.runs.stream(
  thread["thread_id"],
  agent["assistant_id"],
  {
    task: task.task,
  },
);

for await (const chunk of streamResponse) {
  console.log(chunk);
}