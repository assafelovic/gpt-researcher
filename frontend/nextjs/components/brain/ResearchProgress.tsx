"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Data } from "../../types/data";

/**
 * Phase rail for a live research run. Derives Plan / Search / Read / Write
 * progress from the raw websocket event stream so non-technical teammates
 * see a readable storyline instead of a log firehose.
 */

type PhaseId = "plan" | "search" | "read" | "write";

const PHASES: { id: PhaseId; label: string; hint: string }[] = [
  { id: "plan", label: "Planning", hint: "Choosing the agent and outlining sub-questions" },
  { id: "search", label: "Searching", hint: "Querying the web, code graph, and connected tools" },
  { id: "read", label: "Reading", hint: "Scraping and digesting the sources it found" },
  { id: "write", label: "Writing", hint: "Composing the cited report" },
];

const PHASE_EVENTS: Record<PhaseId, string[]> = {
  plan: [
    "agent_generated",
    "starting_research",
    "planning_research",
    "research_plan",
    "generating_subtopics",
    "subtopics_generated",
  ],
  search: [
    "subqueries",
    "running_subquery_research",
    "running_subquery_with_vectorstore_research",
    "added_source_url",
    "scraping_urls",
    "mcp_retrieval",
    "mcp_results",
    "mcp_comprehensive",
    "mcp_comprehensive_run",
  ],
  read: [
    "scraping_content",
    "scraping_complete",
    "scraping_images",
    "fetching_query_content",
    "subquery_context_window",
    "context_combined",
    "research_step_finalized",
    "mcp_research_complete",
  ],
  write: [
    "writing_report",
    "writing_introduction",
    "writing_conclusion",
    "generating_draft_sections",
    "draft_sections_generated",
    "introduction_written",
    "conclusion_written",
    "report_written",
  ],
};

const EVENT_LABELS: Record<string, string> = {
  agent_generated: "Picked a specialist agent",
  starting_research: "Kicking off the research run",
  planning_research: "Planning the research outline",
  research_plan: "Research plan ready",
  subqueries: "Sub-questions chosen",
  running_subquery_research: "Searching a sub-question",
  added_source_url: "Found a source",
  scraping_urls: "Collecting pages to read",
  scraping_content: "Reading sources",
  scraping_complete: "Finished reading sources",
  fetching_query_content: "Pulling page content",
  context_combined: "Combining everything it learned",
  research_step_finalized: "Research step complete",
  mcp_retrieval: "Querying connected tools",
  mcp_results: "Tool results in",
  writing_report: "Writing the report",
  writing_introduction: "Writing the introduction",
  writing_conclusion: "Writing the conclusion",
  report_written: "Report finished",
};

const eventPhase = (content: string): PhaseId | null => {
  for (const phase of PHASES) {
    if (PHASE_EVENTS[phase.id].includes(content)) return phase.id;
  }
  return null;
};

const prettify = (content: string) =>
  EVENT_LABELS[content] ||
  content.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

interface Derived {
  currentPhase: PhaseId;
  reachedIndex: number;
  done: boolean;
  sourceCount: number;
  subqueryCount: number;
  latestLabel: string;
}

const deriveProgress = (orderedData: Data[]): Derived => {
  let reachedIndex = 0;
  let done = false;
  let subqueryCount = 0;
  let latestLabel = "Warming up";
  const sources = new Set<string>();

  for (const item of orderedData as any[]) {
    if (item.type === "path" || item.type === "report_complete") {
      done = true;
      continue;
    }
    if (item.type === "report") {
      reachedIndex = Math.max(reachedIndex, 3);
      latestLabel = "Writing the report";
      continue;
    }
    const content = typeof item.content === "string" ? item.content : "";
    if (!content) continue;
    if (content === "added_source_url" && typeof item.metadata === "string") {
      sources.add(item.metadata);
    }
    if (content === "subqueries" && Array.isArray(item.metadata)) {
      subqueryCount = item.metadata.length;
    }
    const phase = eventPhase(content);
    if (phase) {
      const idx = PHASES.findIndex((p) => p.id === phase);
      reachedIndex = Math.max(reachedIndex, idx);
      latestLabel = prettify(content);
    }
  }

  return {
    currentPhase: PHASES[reachedIndex].id,
    reachedIndex,
    done,
    sourceCount: sources.size,
    subqueryCount,
    latestLabel,
  };
};

const formatElapsed = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s.toString().padStart(2, "0")}s` : `${s}s`;
};

interface ResearchProgressProps {
  orderedData: Data[];
  loading: boolean;
}

export default function ResearchProgress({
  orderedData,
  loading,
}: ResearchProgressProps) {
  const derived = useMemo(() => deriveProgress(orderedData), [orderedData]);
  const startRef = useRef<number>(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const finishedAtRef = useRef<number | null>(null);

  const finished = derived.done || !loading;

  useEffect(() => {
    if (finished) {
      if (finishedAtRef.current === null) {
        finishedAtRef.current = Math.floor(
          (Date.now() - startRef.current) / 1000,
        );
        setElapsed(finishedAtRef.current);
      }
      return;
    }
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [finished]);

  if (orderedData.length === 0) return null;

  return (
    <div className="container mt-2 w-full rounded-lg border border-solid border-gray-700/35 bg-black/25 p-4 shadow-lg backdrop-blur-md">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center">
          {PHASES.map((phase, index) => {
            const isComplete = finished || index < derived.reachedIndex;
            const isCurrent = !finished && index === derived.reachedIndex;
            return (
              <div key={phase.id} className="flex flex-1 items-center last:flex-none">
                <div className="group relative flex items-center gap-2" title={phase.hint}>
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-bold transition-colors ${
                      isComplete
                        ? "border-teal-500/60 bg-teal-500/20 text-teal-300"
                        : isCurrent
                          ? "border-teal-400 bg-teal-400/10 text-teal-200"
                          : "border-white/15 bg-white/[0.03] text-slate-500"
                    }`}
                  >
                    {isComplete ? (
                      <svg viewBox="0 0 12 12" className="h-3 w-3 fill-current">
                        <path d="M4.5 8.1 2.4 6l-.9.9 3 3 6-6-.9-.9z" />
                      </svg>
                    ) : isCurrent ? (
                      <span className="h-2 w-2 animate-pulse rounded-full bg-teal-300" />
                    ) : (
                      index + 1
                    )}
                  </span>
                  <span
                    className={`whitespace-nowrap text-xs font-semibold uppercase tracking-wide ${
                      isCurrent
                        ? "text-teal-200"
                        : isComplete
                          ? "text-slate-300"
                          : "text-slate-600"
                    }`}
                  >
                    {phase.label}
                  </span>
                </div>
                {index < PHASES.length - 1 && (
                  <div
                    className={`mx-3 h-px flex-1 ${
                      finished || index < derived.reachedIndex
                        ? "bg-teal-500/40"
                        : "bg-white/10"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
        <div className="flex shrink-0 items-center gap-4 text-xs text-slate-400">
          {derived.subqueryCount > 0 && (
            <span title="Sub-questions the researcher is answering">
              {derived.subqueryCount} questions
            </span>
          )}
          {derived.sourceCount > 0 && (
            <span title="Unique sources found so far">
              {derived.sourceCount} sources
            </span>
          )}
          <span title="Elapsed time" className="tabular-nums">
            {formatElapsed(elapsed)}
          </span>
        </div>
      </div>
      {!finished && (
        <p className="mt-3 truncate text-xs leading-5 text-slate-400">
          <span className="mr-2 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-teal-300 align-middle" />
          {derived.latestLabel}
        </p>
      )}
    </div>
  );
}
