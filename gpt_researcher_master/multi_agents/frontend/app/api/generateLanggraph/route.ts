import { Client } from "@langchain/langgraph-sdk";
import { EditorAgent } from "../Agents/EditorAgent";
import { ChiefEditorAgent } from "../Agents/ChiefEditorAgent";
import { PublisherAgent } from "../Agents/PublisherAgent";
import { ResearchAgent } from "../Agents/ResearchAgent";
import { ReviewerAgent } from "../Agents/ReviewerAgent";
import { ReviserAgent } from "../Agents/ReviserAgent";
import { WriterAgent } from "../Agents/WriterAgent";

import {task} from "../config/task.js";

export async function POST(request: Request) {
  let { question, sources } = await request.json();

  try {
    const client = new Client();

    console.log('client in route.ts', client)

    const maxSections = task?.task?.max_sections || 5; // Default to 5 sections if undefined
    const initialResearch = task?.initial_research || "";

    const prompt = [{
      role: "system",
      content: "You are a research director. Your goal is to oversee the research project from inception to completion."
    }, {
      role: "user",
      content: `Today's date is ${new Date().toLocaleDateString()}.\nResearch summary report: '${initialResearch}'\n\nYour task is to generate an outline of sections headers for the research project based on the research summary report above.\nYou must generate a maximum of ${maxSections} section headers.\nYou must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\nYou must return nothing but a JSON with the fields 'title' (str) and 'sections' (maximum ${maxSections} section headers) with the following structure: '{title: string research title, date: today's date, sections: ['section header 1', 'section header 2', 'section header 3' ...]}'.`
    }];

    const assistants = await client.assistants.search({
      metadata: null,
      offset: 0,
      limit: 10,
    });

    console.log('assistants in route.ts', assistants);

    const agent = assistants[0];
    const thread = await client.threads.create();
    const messages = [{ role: "human", content: JSON.stringify(prompt) }];

    console.log('Thread: in route.ts', thread);
    console.log('Thread ID: in route.ts', thread["thread_id"]);
    console.log('Assistant ID: in route.ts', agent["assistant_id"]);

    // Create a run
    const run = await client.runs.create(thread["thread_id"], agent["assistant_id"], { input: { messages } });

    console.log('Run ID: in route.ts', run["run_id"]);

    // Example usage of ChiefEditorAgent
    const chiefEditorAgent = new ChiefEditorAgent(task.task);
    await chiefEditorAgent.runResearchTask();

    // Example usage of ResearchAgent
    const researchAgent = new ResearchAgent();
    const researchData = await researchAgent.research(question);

    // Example usage of EditorAgent
    const editorAgent = new EditorAgent();
    // const researchState = {
    //   initial_research: task.initial_research,
    //   task: task.task
    // };
    // const researchPlan = await editorAgent.planResearch(researchState);


    // Example usage of WriterAgent
    const writerAgent = new WriterAgent();
    const writtenSection = await writerAgent.writeSection("Introduction", researchData);
    console.log("Written Section: ", writtenSection);

    // Example usage of PublisherAgent
    const publisherAgent = new PublisherAgent();
    const publishedReport = await publisherAgent.publishReport(writtenSection);
    console.log("Published Report: ", publishedReport);

    // Example usage of ReviewerAgent
    const reviewerAgent = new ReviewerAgent();
    const reviewFeedback = await reviewerAgent.reviewDraft(writtenSection);
    console.log("Review Feedback: ", reviewFeedback);

    // Example usage of ReviserAgent
    const reviserAgent = new ReviserAgent();
    const revisedDraft = await reviserAgent.reviseDraft(writtenSection, reviewFeedback);
    console.log("Revised Draft: ", revisedDraft);

    return new Response(JSON.stringify(revisedDraft), {
      headers: new Headers({
        "Cache-Control": "no-cache",
      }),
    });
  } catch (e) {
    console.log("Error is: ", e);
    return new Response(e, { status: 202 });
  }
}