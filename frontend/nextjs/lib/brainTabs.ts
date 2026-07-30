export type BrainTabId =
  | "ask"
  | "codebase"
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
    id: "codebase",
    label: "Codebase",
    description: "Estate capabilities and can-we-do-X",
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
