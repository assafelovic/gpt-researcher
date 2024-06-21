import { Client } from "@langchain/langgraph-sdk";

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

// Start a streaming run
const task = {
  "query": "What is GPT Researcher?",
  "max_sections": 3,
  "publish_formats": {
    "markdown": true,
    "pdf": true,
    "docx": true
  },
  "follow_guidelines": false,
  "model": "gpt-4o",
  "guidelines": [],
  "verbose": true
}

const streamResponse = client.runs.stream(
  thread["thread_id"],
  agent["assistant_id"],
  {
    task: task,
  },
);

for await (const chunk of streamResponse) {
  console.log(chunk);
}