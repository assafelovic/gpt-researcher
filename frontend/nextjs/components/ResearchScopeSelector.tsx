"use client";

import { useEffect, useState } from "react";
import { HLTResearchScope } from "@/types/data";
import { normalizeHLTResearchScope, selectedScopeCount } from "@/lib/hltResearchScope";

type ResearchScopeSelectorProps = {
  value?: HLTResearchScope;
  onChange: (next: HLTResearchScope) => void;
  compact?: boolean;
};

type ScopeKey = "codebase" | "cms" | "metrics" | "firecrawl";

const scopeOptions: Array<{
  key: ScopeKey;
  label: string;
  eyebrow: string;
  description: string;
}> = [
  {
    key: "codebase",
    label: "Code files",
    eyebrow: "GitHub + repo maps",
    description: "Pull implementation context into the research run.",
  },
  {
    key: "cms",
    label: "CMS + Registry",
    eyebrow: "Katailyst",
    description: "Use internal entities, playbooks, docs, and KB context.",
  },
  {
    key: "metrics",
    label: "Metrics",
    eyebrow: "Metabase-ready",
    description: "Include performance data when a metrics MCP is configured.",
  },
  {
    key: "firecrawl",
    label: "High-quality crawl",
    eyebrow: "Firecrawl",
    description: "Prefer richer extraction for difficult pages.",
  },
];

const depthOptions: Array<{ value: HLTResearchScope["depth"]; label: string }> = [
  { value: "fast", label: "Fast" },
  { value: "balanced", label: "Balanced" },
  { value: "deep", label: "Deep" },
];

type ReadinessStatus = "ready" | "partial" | "unavailable" | "inactive";

type HLTReadiness = {
  integrations?: Partial<Record<ScopeKey, {
    status?: ReadinessStatus;
    missing?: string[];
  }>>;
};

const badgeText: Record<ReadinessStatus, string> = {
  ready: "Ready",
  partial: "Partial",
  unavailable: "Needs config",
  inactive: "Checking",
};

const badgeClass: Record<ReadinessStatus, string> = {
  ready: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
  partial: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  unavailable: "border-slate-500/30 bg-slate-500/10 text-slate-300",
  inactive: "border-slate-500/20 bg-white/[0.04] text-slate-400",
};

export default function ResearchScopeSelector({
  value,
  onChange,
  compact = false,
}: ResearchScopeSelectorProps) {
  const scope = normalizeHLTResearchScope(value);
  const count = selectedScopeCount(scope);
  const [readiness, setReadiness] = useState<HLTReadiness | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/hlt/readiness", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then((data) => {
        if (!cancelled && data) {
          setReadiness(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setReadiness(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const update = (patch: Partial<HLTResearchScope>) => {
    onChange({ ...scope, ...patch });
  };

  return (
    <section
      className={`mx-auto w-full max-w-[980px] px-4 ${compact ? "mt-4" : "mt-2"}`}
      aria-label="Research scope"
    >
      <div className="rounded-2xl border border-white/10 bg-[#0A0A0B]/72 p-3 shadow-[0_24px_70px_rgba(0,0,0,0.32)] backdrop-blur-xl sm:p-4">
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-blue-300">
              Research Scope
            </div>
            <div className="mt-1 text-sm text-slate-300">
              {count > 0 ? `${count} internal source${count === 1 ? "" : "s"} selected` : "Web research only"}
            </div>
          </div>

          <div className="inline-flex rounded-full border border-white/10 bg-white/5 p-1">
            {depthOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => update({ depth: option.value })}
                className={`h-8 rounded-full px-3 text-xs font-semibold transition-colors ${
                  scope.depth === option.value
                    ? "bg-[#155EEF] text-white shadow-[0_0_24px_rgba(21,94,239,0.28)]"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className={`grid gap-2 ${compact ? "grid-cols-1" : "sm:grid-cols-2 lg:grid-cols-4"}`}>
          {scopeOptions.map((option) => {
            const selected = scope[option.key];
            const status = readiness?.integrations?.[option.key]?.status || "inactive";
            return (
              <label
                key={option.key}
                className={`group flex min-h-[112px] cursor-pointer flex-col justify-between rounded-xl border p-3 transition-all ${
                  selected
                    ? "border-[#155EEF]/80 bg-[#155EEF]/14 shadow-[0_16px_36px_rgba(21,94,239,0.18)]"
                    : "border-white/10 bg-white/[0.045] hover:border-white/20 hover:bg-white/[0.07]"
                }`}
              >
                <span className="flex items-start justify-between gap-3">
                  <span>
                    <span className="block text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
                      {option.eyebrow}
                    </span>
                    <span className="mt-1 flex flex-wrap items-center gap-2">
                      <span className="block text-sm font-semibold text-white">{option.label}</span>
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${badgeClass[status]}`}>
                        {badgeText[status]}
                      </span>
                    </span>
                  </span>
                  <span
                    className={`mt-0.5 flex h-5 w-9 items-center rounded-full p-0.5 transition-colors ${
                      selected ? "bg-[#155EEF]" : "bg-slate-700"
                    }`}
                  >
                    <span
                      className={`h-4 w-4 rounded-full bg-white transition-transform ${
                        selected ? "translate-x-4" : "translate-x-0"
                      }`}
                    />
                  </span>
                </span>
                <span className="mt-3 text-xs leading-5 text-slate-400">{option.description}</span>
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={selected}
                  onChange={() => update({ [option.key]: !selected } as Partial<HLTResearchScope>)}
                />
              </label>
            );
          })}
        </div>
      </div>
    </section>
  );
}
