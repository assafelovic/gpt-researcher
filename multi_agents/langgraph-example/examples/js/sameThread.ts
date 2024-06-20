// How to run multiple agents on the same thread
import { Client } from "@langchain/langgraph-sdk";

/* 
In LangGraph API, a thread is not explicitly associated with a particular agent.
This means that you can run multiple agents on the same thread.
In this example, we will create two agents and then call them both on the same thread.
*/

async function main() {
  const client = new Client();
  // const openaiAssistant = await client.assistants.create({ graphId: "agent", config: { configurable: { model_name: "openai" } }});
  const defaultAssistant = await client.assistants.create({ graphId: "agent" });
  const openaiAssistant = await client.assistants.create({
    graphId: "agent",
    config: { configurable: { model_name: "openai" } },
  });

  console.log("Default assistant", defaultAssistant);
  // We can see that this assistant has saved the config
  console.log("OpenAI assistant", openaiAssistant);
  const thread = await client.threads.create();
  let input = { messages: [{ role: "user", content: "who made you?" }] };

  for await (const event of client.runs.stream(
    thread.thread_id,
    openaiAssistant.assistant_id,
    { input, streamMode: "updates" }
  )) {
    console.log(JSON.stringify(event.data));
    console.log("\n\n");
  }

  input = { messages: [{ role: "user", content: "and you?" }] };
  for await (const event of client.runs.stream(
    thread.thread_id,
    defaultAssistant.assistant_id,
    { input, streamMode: "updates" }
  )) {
    console.log(JSON.stringify(event.data));
    console.log("\n\n");
  }
}

main();
