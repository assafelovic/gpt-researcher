import { Client } from "@langchain/langgraph-sdk";
import { ResearchAgent } from "./ResearchAgent";
import { task } from "../config/task.js";

export class EditorAgent {
  private client: Client;

  constructor() {
    this.client = new Client();
  }

  async planResearch(researchState: any) {
    const maxSections = researchState?.task?.max_sections || 5; // Default to 5 sections if undefined
    const initialResearch = researchState?.initial_research || "";

    const prompt = [{
      role: "system",
      content: "You are a research director. Your goal is to oversee the research project from inception to completion."
    }, {
      role: "user",
      content: `Today's date is ${new Date().toLocaleDateString()}.\nResearch summary report: '${initialResearch}'\n\nYour task is to generate an outline of sections headers for the research project based on the research summary report above.\nYou must generate a maximum of ${maxSections} section headers.\nYou must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\nYou must return nothing but a JSON with the fields 'title' (str) and 'sections' (maximum ${maxSections} section headers) with the following structure: '{title: string research title, date: today's date, sections: ['section header 1', 'section header 2', 'section header 3' ...]}'.`
    }];

    const assistants = await this.client.assistants.search({
      metadata: null,
      offset: 0,
      limit: 10,
    });

    console.log('assistants', assistants);

    const agent = assistants[0];
    const thread = await this.client.threads.create();
    const messages = [{ role: "human", content: JSON.stringify(prompt) }];

    console.log('Thread:', thread);
    console.log('Thread ID:', thread["thread_id"]);
    console.log('Assistant ID:', agent["assistant_id"]);

    // Create a run
    const run = await this.client.runs.create(thread["thread_id"], agent["assistant_id"], { input: { messages } });

    console.log('Run ID in EditorAgent.ts:', run["run_id"]);

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