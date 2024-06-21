import { Client } from "@langchain/langgraph-sdk";

export class PublisherAgent {
  private client: Client;

  constructor() {
    this.client = new Client();
  }

  async publishReport(report: any) {
    const prompt = [{
      role: "system",
      content: "You are a publisher. Your goal is to publish a research report."
    }, {
      role: "user",
      content: `Research report: ${JSON.stringify(report)}\n\nPublish the report in the desired format.`
    }];

    // Search for assistants
    const assistants = await this.client.assistants.search({
      metadata: null,
      offset: 0,
      limit: 10,
    });

    const agent = assistants[0];
    const thread = await this.client.threads.create();
    const messages = [{ role: "human", content: JSON.stringify(prompt) }];

    // Create a run
    const run = await this.client.runs.create(thread["thread_id"], agent["assistant_id"], { input: { messages } });

    return run;
  }
}