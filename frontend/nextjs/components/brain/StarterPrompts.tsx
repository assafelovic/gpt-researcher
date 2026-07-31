"use client";

import { BrainTabId } from "@/lib/brainTabs";
import { STARTER_PROMPTS, StarterPrompt } from "@/lib/starterPrompts";

type Props = {
  tab: BrainTabId;
  onSelect: (prompt: StarterPrompt) => void;
};

export default function StarterPrompts({ tab, onSelect }: Props) {
  const prompts = STARTER_PROMPTS[tab] || [];
  if (prompts.length === 0) return null;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-2 pt-4">
      <p className="mb-2 text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        What can I ask?
      </p>
      <div className="flex flex-wrap items-center justify-center gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt.label}
            type="button"
            title={prompt.prompt}
            onClick={() => onSelect(prompt)}
            className="rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-teal-400/40 hover:bg-teal-400/10 hover:text-white"
          >
            {prompt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
