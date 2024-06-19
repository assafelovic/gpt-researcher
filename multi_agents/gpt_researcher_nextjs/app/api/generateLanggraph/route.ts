import { Client } from "@langchain/langgraph-sdk";
import { ResearchAgent } from "../ResearchAgent/ResearchAgent";
import { EditorAgent } from "../EditorAgent/EditorAgent";
import { ChiefEditorAgent } from "../ChiefEditorAgent/ChiefEditorAgent";
import { WriterAgent } from "../WriterAgent/WriterAgent";
import { PublisherAgent } from "../PublisherAgent/PublisherAgent";
import { ReviewerAgent } from "../ReviewerAgent/ReviewerAgent";
import { ReviserAgent } from "../ReviserAgent/ReviserAgent";

export async function POST(request: Request) {
  let { question, sources } = await request.json();

  try {
    const client = new Client();

    // Example usage of ResearchAgent
    const researchAgent = new ResearchAgent();
    const researchData = await researchAgent.research(question);

    // Example usage of EditorAgent
    const editorAgent = new EditorAgent();
    const researchPlan = await editorAgent.planResearch({ initial_research: researchData });

    // Example usage of ChiefEditorAgent
    const chiefEditorAgent = new ChiefEditorAgent({ query: question });
    await chiefEditorAgent.runResearchTask();

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