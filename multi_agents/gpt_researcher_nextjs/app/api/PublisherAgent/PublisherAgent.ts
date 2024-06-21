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

    // Assuming the correct method is `invokeAssistant` instead of `invoke`
    const response = await this.client.invokeAssistant({
      assistant_id: "publisher_model",
      input: { messages: prompt }
    });

    return response;
  }
}