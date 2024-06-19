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

    const response = await this.client.assistants.invoke({
      assistant_id: "reviser_model",
      input: { messages: prompt }
    });

    return response;
  }
}