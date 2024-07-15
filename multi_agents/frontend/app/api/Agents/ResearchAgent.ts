import { Client } from "@langchain/langgraph-sdk";

export class ResearchAgent {
  private client: Client;

  constructor() {
    this.client = new Client();
  }

  async research(query: string, researchReport: string = "research_report", parentQuery: string = "", verbose: boolean = true, source: string = "web") {
    const assistants = await this.client.assistants.search({
      metadata: null,
      offset: 0,
      limit: 10,
    });

    const agent = assistants[0];
    const thread = await this.client.threads.create();
    const messages = [{ role: "human", content: query }];

    const streamResponse = this.client.runs.stream(
      thread["thread_id"],
      agent["assistant_id"],
      {
        input: { messages },
      },
    );

    for await (const chunk of streamResponse) {
      console.log(chunk);
    }

    return streamResponse;
  }
}