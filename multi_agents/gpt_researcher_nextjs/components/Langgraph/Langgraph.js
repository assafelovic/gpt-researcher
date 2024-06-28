import { Client } from "@langchain/langgraph-sdk";
import { task } from '../../config/task';
import { getHost } from '../../helpers/getHost';

export async function startLanggraphResearch(newQuestion, report_source, onUpdate) {
    // Update the task query with the new question
    task.task.query = newQuestion;
    task.task.source = report_source;
    const host = getHost({purpose: 'langgraph-gui'});
  
    const client = new Client({apiUrl: host});
  
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

    // Start polling
    startPolling(thread["thread_id"], null, onUpdate);

    return {streamResponse, host, thread_id: thread["thread_id"]};
}

async function startPolling(threadId, checkpointId, onUpdate) {
  const client = new Client();
  let previousState = null;

  const poll = async () => {
    try {
      const currentState = await client.threads.getState(threadId, checkpointId);
      if (JSON.stringify(currentState) !== JSON.stringify(previousState)) {
        previousState = currentState;
        onUpdate(currentState);
      }
    } catch (error) {
      console.error('Error polling state:', error);
    }
  };

  setInterval(poll, 2000); // Poll every 2 seconds
}