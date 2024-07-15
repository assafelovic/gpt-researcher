import { Client } from "@langchain/langgraph-sdk";

export class ReviserAgent {
  private client: Client;

  constructor() {
    this.client = new Client();
  }

  async reviseDraft(draft: any, feedback: any) {
    const prompt = [{
      role: "system",
      content: "You are a reviser. Your goal is to revise a research draft based on feedback."
    }, {
      role: "user",
      content: `Research draft: ${JSON.stringify(draft)}\nFeedback: ${JSON.stringify(feedback)}\n\nRevise the draft based on the feedback.`
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