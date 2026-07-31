import { BrainTabId } from "@/lib/brainTabs";
import { HLTResearchScope } from "@/types/data";

export type StarterPrompt = {
  label: string;
  prompt: string;
  /** Scope toggles applied before the run launches. */
  scope?: Partial<HLTResearchScope>;
};

/**
 * "What can I ask?" chips per Brain tab. Each chip launches a real research
 * run with the right scopes pre-set, so non-technical teammates get a great
 * first run without learning the toggles.
 */
export const STARTER_PROMPTS: Record<BrainTabId, StarterPrompt[]> = {
  ask: [
    {
      label: "Trending in nurse forums this month",
      prompt:
        "What are the most upvoted topics and complaints in nurse forums (r/nursing, r/StudentNurse, allnurses) over the last month? Quote nurses verbatim with links.",
      scope: { audience: true, firecrawl: true, depth: "deep" },
    },
    {
      label: "Competitor teardown",
      prompt:
        "Do a competitive teardown of the top sites helping new-grad nurses find their first job. What do they do better than nursingmastery.com, and what do we do better?",
      scope: { recruiting: true, firecrawl: true, depth: "deep" },
    },
    {
      label: "Best-on-earth study",
      prompt:
        "What do the best career/job platforms in ANY industry do that nurse recruiting hasn't copied yet?",
      scope: { audience: true, recruiting: true, mode: "top1", depth: "deep" },
    },
  ],
  audience: [
    {
      label: "Top pains right now",
      prompt:
        "What are the top 5 pain points nurses and nursing students are voicing right now? Rank by engagement, quote verbatim with receipts, and compare against our internal pain-points list.",
      scope: { audience: true, firecrawl: true, depth: "deep" },
    },
    {
      label: "In their words: first job",
      prompt:
        "Collect the most upvoted verbatim quotes about landing the first nursing job from the last 3 months. Group by theme.",
      scope: { audience: true, firecrawl: true, depth: "deep" },
    },
    {
      label: "What changed this month?",
      prompt:
        "Compare current nurse forum discussions to our internal audience corpus: what is new or growing that the corpus doesn't capture yet?",
      scope: { audience: true, firecrawl: true, depth: "deep" },
    },
  ],
  codebase: [
    {
      label: "Can we do X?",
      prompt:
        "Can our estate generate a personalized pay report for a nurse from ScraperVault data and email it? Which repos are involved and what's missing?",
      scope: { codebase: true, cms: true, depth: "deep" },
    },
    {
      label: "How does the apply funnel work?",
      prompt:
        "Explain the nurse apply funnel end to end across nursing-mastery and ScraperVault: pages, APIs, data stored, and drop-off points a non-engineer should know.",
      scope: { codebase: true, depth: "deep" },
    },
  ],
  library: [
    {
      label: "Build on past research",
      prompt:
        "Summarize what our past research already established about nurse recruiting channels, then identify the biggest open question and answer it.",
      scope: { audience: true, depth: "deep" },
    },
  ],
  vision: [
    {
      label: "Does this fit the vision?",
      prompt:
        "Based on the vision docs, would a paid resume-review service for new grads fit our product north star? Argue both sides, then recommend.",
      scope: { depth: "balanced" },
    },
  ],
  changelog: [
    {
      label: "Explain recent shipping",
      prompt:
        "Summarize what shipped across the estate in the last 3 weeks in plain language for a non-technical teammate, and what it unlocks next.",
      scope: { codebase: true, depth: "balanced" },
    },
  ],
  roadmap: [
    {
      label: "Risks to the current milestone",
      prompt:
        "Looking at the active roadmap milestones, what external evidence (market, competitors, audience complaints) suggests we should re-order priorities?",
      scope: { audience: true, firecrawl: true, depth: "deep" },
    },
  ],
};
