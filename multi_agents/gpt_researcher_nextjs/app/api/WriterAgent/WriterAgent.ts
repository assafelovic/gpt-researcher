import { Client } from "@langchain/langgraph-sdk";

export class WriterAgent {
  private client: Client;

  constructor() {
    this.client = new Client();
  }

  async writeSection(sectionTitle: string, researchData: any) {
    const prompt = [{
      role: "system",
      content: "You are a writer. Your goal is to write a section of a research report."
    }, {
      role: "user",
      content: `Section title: ${sectionTitle}\nResearch data: ${JSON.stringify(researchData)}\n\nWrite a detailed section based on the research data.`
    }];

    const response = await this.client.assistants.invoke({
      assistant_id: "writer_model",
      input: { messages: prompt }
    });

    return response;
  }
}