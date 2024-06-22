import { Client } from "@langchain/langgraph-sdk";
import { task } from '../../config/task';

export async function startLanggraphResearch(newQuestion) {
    // Update the task query with the new question
    task.task.query = newQuestion;
  
    const client = new Client(task);
  
    // List all assistants
    const assistants = await client.assistants.search({
      metadata: null,
      offset: 0,
      limit: 10,
    });
  
    console.log('assistants: ', assistants);
  
    // We auto-create an assistant for each graph you register in config.
    const agent = assistants[0];
  
    // Start a new thread
    const thread = await client.threads.create();
  
    // Start a streaming run
    const input = { task: { query: newQuestion } };
  
    const streamResponse = client.runs.stream(
      thread["thread_id"],
      agent["assistant_id"],
      {
        input,
      },
    );
  
    for await (const chunk of streamResponse) {
      console.log(chunk);
    }
}