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

    const response = await this.client.assistants.invoke({
      assistant_id: "publisher_model",
      input: { messages: prompt }
    });

    return response;
  }
}