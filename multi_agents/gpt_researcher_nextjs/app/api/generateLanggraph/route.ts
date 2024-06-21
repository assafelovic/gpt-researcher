import { Client } from "@langchain/langgraph-sdk";
import { ResearchAgent } from "../ResearchAgent/ResearchAgent";
import { EditorAgent } from "../EditorAgent/EditorAgent";
import { ChiefEditorAgent } from "../ChiefEditorAgent/ChiefEditorAgent";
import { WriterAgent } from "../WriterAgent/WriterAgent";
import { PublisherAgent } from "../PublisherAgent/PublisherAgent";
import { ReviewerAgent } from "../ReviewerAgent/ReviewerAgent";
import { ReviserAgent } from "../ReviserAgent/ReviserAgent";

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

    try {
      // Poll the run until it completes
      let finalRunStatus = await client.runs.get(thread["thread_id"], run["run_id"]);
      while (finalRunStatus.status !== "success") {
        await new Promise((resolve) => setTimeout(resolve, 1000)); // Polling every second
        finalRunStatus = await client.runs.get(thread["thread_id"], run["run_id"]);
      }

      console.log('Final run status in route.ts', finalRunStatus);

      // Get the final results
      const results = await client.runs.listEvents(thread["thread_id"], run["run_id"]);

      // The results are sorted by time, so the most recent (final) step is the 0 index
      const finalResult = results[0];
      console.log('Final result in route.ts', finalResult);

      // Get the content of the final message
      const finalMessages = (finalResult.data as Record<string, any>)["output"]["messages"];
      const finalMessageContent = finalMessages[finalMessages.length - 1].content;
      console.log('Final message content in route.ts', finalMessageContent);

      // Ensure the response is a valid JSON string
      if (typeof finalMessageContent === 'string') {
        return JSON.parse(finalMessageContent);
      } else {
        console.error("Response is not a valid JSON string:", finalMessageContent);
        throw new Error("Invalid JSON response");
      }
    } catch (error) {
      console.error("Failed to fetch response:", error);
      throw error;
    }

    // Example usage of ChiefEditorAgent
    const chiefEditorAgent = new ChiefEditorAgent(task.task);
    await chiefEditorAgent.runResearchTask();

    // Example usage of ResearchAgent
    const researchAgent = new ResearchAgent();
    const researchData = await researchAgent.research(question);

    // Example usage of EditorAgent
    const editorAgent = new EditorAgent();
    const researchState = {
      initial_research: task.initial_research,
      task: task.task
    };
    const researchPlan = await editorAgent.planResearch(researchState);


    // Example usage of WriterAgent
    const writerAgent = new WriterAgent();
    const writtenSection = await writerAgent.writeSection("Introduction", researchData);

    // Example usage of PublisherAgent
    const publisherAgent = new PublisherAgent();
    const publishedReport = await publisherAgent.publishReport(writtenSection);

    // Example usage of ReviewerAgent
    const reviewerAgent = new ReviewerAgent();
    const reviewFeedback = await reviewerAgent.reviewDraft(writtenSection);

    // Example usage of ReviserAgent
    const reviserAgent = new ReviserAgent();
    const revisedDraft = await reviserAgent.reviseDraft(writtenSection, reviewFeedback);

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