export type BrainTabId =
  | "ask"
  | "audience"
  | "codebase"
  | "library"
  | "vision"
  | "changelog"
  | "roadmap";

export type BrainTab = {
  id: BrainTabId;
  label: string;
  description: string;
};

export const BRAIN_TABS: BrainTab[] = [
  {
    id: "ask",
    label: "Ask",
    description: "Deep research with Mastery scope toggles",
  },
  {
    id: "audience",
    label: "Audience",
    description: "What nurses actually say — pains, quotes, trends",
  },
  {
    id: "codebase",
    label: "Codebase",
    description: "Estate capabilities and can-we-do-X",
  },
  {
    id: "library",
    label: "Library",
    description: "Past research, searchable — knowledge compounds",
  },
  {
    id: "vision",
    label: "Vision",
    description: "Product north star the researcher can cite",
  },
  {
    id: "changelog",
    label: "Changelog",
    description: "What shipped, visually",
  },
  {
    id: "roadmap",
    label: "Roadmap",
    description: "Linear milestones and what’s next",
  },
];
