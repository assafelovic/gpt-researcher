"use client";

import { HLTResearchScope } from "@/types/data";
import { normalizeHLTResearchScope } from "@/lib/hltResearchScope";

type ResearchScopeSelectorProps = {
  value?: HLTResearchScope;
  onChange: (next: HLTResearchScope) => void;
  compact?: boolean;
};

type ScopeKey = "firecrawl" | "qbank" | "media" | "codebase" | "cms" | "metrics";

const scopeOptions: Array<{
  key: ScopeKey;
  label: string;
  title: string;
}> = [
  {
    key: "firecrawl",
    label: "Deep web",
    title: "Use deeper public web extraction.",
  },
  {
    key: "qbank",
    label: "QBank",
    title:
      "Use read-only corporate CMS and question-bank context through the protected Katailyst tool path.",
  },
  {
    key: "media",
    label: "Media",
    title: "Search the Cloudinary media library through the server-side HLT media connection.",
  },
  {
    key: "codebase",
    label: "Code",
    title: "Search selected code context.",
  },
  {
    key: "cms",
    label: "Registry",
    title:
      "Search Katailyst entities, playbooks, docs, skills, and knowledge-base context.",
  },
  {
    key: "metrics",
    label: "Metrics",
    title:
      "Include analytics and performance context when metrics access is configured.",
  },
];

const depthOptions: Array<{ value: HLTResearchScope["depth"]; label: string }> =
  [
    { value: "fast", label: "Fast" },
    { value: "balanced", label: "Balanced" },
    { value: "deep", label: "Deep" },
  ];

export default function ResearchScopeSelector({
  value,
  onChange,
  compact = false,
}: ResearchScopeSelectorProps) {
  const scope = normalizeHLTResearchScope(value);

  const update = (patch: Partial<HLTResearchScope>) => {
    onChange({ ...scope, ...patch });
  };

  return (
    <section
      className={`mx-auto w-full max-w-[820px] px-4 ${compact ? "mt-4" : "mt-0"}`}
      aria-label="Research scope"
    >
      <div className="flex flex-col items-center justify-center gap-2.5">
        <div className="inline-flex w-fit rounded-md border border-white/10 bg-white/[0.04] p-0.5 backdrop-blur">
          {depthOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => update({ depth: option.value })}
              className={`h-7 rounded px-3 text-xs font-semibold transition-colors ${
                scope.depth === option.value
                  ? "bg-[#155EEF] text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        <div
          className={`flex flex-wrap justify-center gap-1.5 ${compact ? "flex-col" : ""}`}
        >
          {scopeOptions.map((option) => {
            const selected = scope[option.key];
            return (
              <label
                key={option.key}
                title={option.title}
                className={`group flex h-8 cursor-pointer items-center gap-1.5 rounded-md border px-2.5 transition-all ${
                  selected
                    ? "bg-[#155EEF]/14 border-[#155EEF]/75 text-white"
                    : "border-white/10 bg-white/[0.04] text-slate-300 hover:border-white/20 hover:bg-white/[0.07]"
                }`}
              >
                <span className="truncate text-xs font-medium">
                  {option.label}
                </span>
                <span
                  className="flex h-4 w-4 items-center justify-center rounded-full border border-white/10 text-slate-500 transition-colors group-hover:text-slate-300"
                  aria-hidden="true"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-2.5 w-2.5"
                  >
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </span>
                <span
                  className={`flex h-4 w-7 shrink-0 items-center rounded-full p-0.5 transition-colors ${
                    selected ? "bg-[#155EEF]" : "bg-slate-700/80"
                  }`}
                >
                  <span
                    className={`h-3 w-3 rounded-full bg-white transition-transform ${
                      selected ? "translate-x-3" : "translate-x-0"
                    }`}
                  />
                </span>
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={selected}
                  onChange={() =>
                    update({
                      [option.key]: !selected,
                    } as Partial<HLTResearchScope>)
                  }
                />
              </label>
            );
          })}
        </div>
      </div>
    </section>
  );
}
