import { Client } from "@langchain/langgraph-sdk";
import { ResearchAgent } from "../ResearchAgent/ResearchAgent";

export class EditorAgent {
  private client: Client;

  constructor() {
    this.client = new Client();
  }

  async planResearch(researchState: any) {
    const prompt = [{
      role: "system",
      content: "You are a research director. Your goal is to oversee the research project from inception to completion."
    }, {
      role: "user",
      content: `Today's date is ${new Date().toLocaleDateString()}.\nResearch summary report: '${researchState.initial_research}'\n\nYour task is to generate an outline of sections headers for the research project based on the research summary report above.\nYou must generate a maximum of ${researchState.task.max_sections} section headers.\nYou must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\nYou must return nothing but a JSON with the fields 'title' (str) and 'sections' (maximum ${researchState.task.max_sections} section headers) with the following structure: '{title: string research title, date: today's date, sections: ['section header 1', 'section header 2', 'section header 3' ...]}'.`
    }];

    const response = await this.client.assistants.invoke({
      assistant_id: researchState.task.model,
      input: { messages: prompt }
    });

    return JSON.parse(response);
  }

  async runParallelResearch(researchState: any) {
    const researchAgent = new ResearchAgent();
    const queries = researchState.sections;
    const title = researchState.title;

    const tasks = queries.map(query => researchAgent.research(query, "research_report", title));
    const results = await Promise.all(tasks);

    return { research_data: results };
  }
}