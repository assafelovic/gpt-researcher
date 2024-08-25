import { Client } from "@langchain/langgraph-sdk";

export class ReviewerAgent {
  private client: Client;

  constructor() {
    this.client = new Client();
  }

  async reviewDraft(draft: any) {
    const prompt = [{
      role: "system",
      content: "You are a reviewer. Your goal is to review a research draft."
    }, {
      role: "user",
      content: `Research draft: ${JSON.stringify(draft)}\n\nReview the draft and provide feedback.`
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