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

    // Assuming the correct method is createRun
    const assistants = await this.client.assistants.search({
      metadata: null,
      offset: 0,
      limit: 10,
    });

    const agent = assistants[0];
    const thread = await this.client.threads.create();
    const messages = [{ role: "human", content: JSON.stringify(prompt) }];

    const run = this.client.runs.create(thread["thread_id"], agent["assistant_id"], { input: { messages } });

    // Poll the run until it completes
    setInterval(async ()=>{
      let finalRunStatus = await this.client.runs.get(thread["thread_id"], run["run_id"]).then(res=>res);
      console.log('finalRunStatus in WriterAgent.ts:', finalRunStatus)
      if (finalRunStatus.status === "failed") {
        throw new Error(`Run failed with message: ${finalRunStatus.message}`);
      } else if (finalRunStatus.status == "success") {
        console.log('Run completed successfully', finalRunStatus);
        
        // Get the final results
        const results = await this.client.runs.listEvents(thread["thread_id"], run["run_id"]);

        // The results are sorted by time, so the most recent (final) step is the 0 index
        const finalResult = results[0];
        const finalMessages = (finalResult.data as Record<string, any>)["output"]["messages"];
        const finalMessageContent = finalMessages[finalMessages.length - 1].content;

        // Ensure the response is a valid JSON string
        if (typeof finalMessageContent === 'string') {
          return JSON.parse(finalMessageContent);
        } else {
          console.error("Response is not a valid JSON string:", finalMessageContent);
          throw new Error("Invalid JSON response");
        }
      }
    }, 5000); // Polling every second

  }
}