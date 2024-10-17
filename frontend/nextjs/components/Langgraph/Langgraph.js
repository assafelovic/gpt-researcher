import { Client } from "@langchain/langgraph-sdk";
import { task } from '../../config/task';

export async function startLanggraphResearch(newQuestion, report_source, langgraphHostUrl) {
    // Retrieve apiVariables from localStorage
    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};

    // Update the task query with the new question
    task.task.query = newQuestion;
    task.task.source = report_source;
    const host = langgraphHostUrl;
    
    // Use apiVariables.LANGCHAIN_API_KEY instead of hardcoded authToken
    const authToken = apiVariables.LANGCHAIN_API_KEY;

    const client = new Client({
        apiUrl: host,
        defaultHeaders: {
            'Content-Type': 'application/json',
            'X-Api-Key': authToken
        }
    });
  
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
    const input = task;
  
    const streamResponse = client.runs.stream(
      thread["thread_id"],
      agent["assistant_id"],
      {
        input,
      },
    );

    return {streamResponse, host, thread_id: thread["thread_id"]};
}