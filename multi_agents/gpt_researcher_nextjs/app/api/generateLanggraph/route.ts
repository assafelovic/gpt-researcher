import { Client } from "@langchain/langgraph-sdk";

export async function POST(request: Request) {
  let { question, sources } = await request.json();

  try {
    const client = new Client();

    // List all assistants
    const assistants = await client.assistants.search({
      metadata: null,
      offset: 0,
      limit: 10,
    });

    // We auto-create an assistant for each graph you register in config.
    const agent = assistants[0];

    // Start a new thread
    const thread = await client.threads.create();

    // Start a streaming run
    const messages = [{ role: "human", content: question }];

    const streamResponse = client.runs.stream(
      thread["thread_id"],
      agent["assistant_id"],
      {
        input: { messages },
      },
    );

    for await (const chunk of streamResponse) {
      console.log(chunk);
    }

    return new Response(streamResponse, {
      headers: new Headers({
        "Cache-Control": "no-cache",
      }),
    });
  } catch (e) {
    // If for some reason streaming fails, we can just call it without streaming
    
    console.log("Error is: ", e);
    return new Response(e, { status: 202 });
  }
}