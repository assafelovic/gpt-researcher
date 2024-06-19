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

    const response = await this.client.assistants.invoke({
      assistant_id: "reviewer_model",
      input: { messages: prompt }
    });

    return response;
  }
}