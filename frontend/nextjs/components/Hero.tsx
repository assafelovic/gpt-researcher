import React, { FC, useEffect, useState } from "react";
import InputArea from "./ResearchBlocks/elements/InputArea";
import { motion } from "framer-motion";
import { hltBranding } from "@/lib/hltBranding";
import ResearchScopeSelector from "@/components/ResearchScopeSelector";
import { ChatBoxSettings, HLTResearchScope } from "@/types/data";
import { normalizeHLTResearchScope } from "@/lib/hltResearchScope";

type THeroProps = {
  promptValue: string;
  setPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleDisplayResult: (query: string) => void;
  chatBoxSettings?: ChatBoxSettings;
  setChatBoxSettings?: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
};

const Hero: FC<THeroProps> = ({
  promptValue,
  setPromptValue,
  handleDisplayResult,
  chatBoxSettings,
  setChatBoxSettings,
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleScopeChange = (scope: HLTResearchScope) => {
    const normalized = normalizeHLTResearchScope(scope);
    setChatBoxSettings?.((prev) => ({
      ...prev,
      hlt_research_scope: normalized,
      report_type: normalized.depth === "deep" ? "deep" : prev.report_type,
      mcp_enabled:
        prev.mcp_enabled ||
        normalized.codebase ||
        normalized.cms ||
        normalized.qbank ||
        normalized.metrics,
      mcp_strategy: normalized.depth === "fast" ? "fast" : "deep",
    }));
  };

  const handleExampleSearch = (query: string) => {
    setPromptValue(query);
    handleDisplayResult(query);
  };

  const fadeInUp = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="relative mt-[-56px] flex min-h-[440px] items-start overflow-visible pb-5 pt-[74px] sm:min-h-[470px]">
      <motion.div
        initial="hidden"
        animate={isVisible ? "visible" : "hidden"}
        variants={fadeInUp}
        transition={{ duration: 0.35 }}
        className="flex w-full flex-col items-center justify-start py-2"
      >
        <motion.h1
          variants={fadeInUp}
          transition={{ duration: 0.35, delay: 0.03 }}
          className="max-w-[620px] px-4 pt-2 text-center text-lg font-semibold leading-tight text-white sm:text-xl md:text-2xl"
        >
          {hltBranding.enabled
            ? "What should Mastery research?"
            : "What would you like to research next?"}
        </motion.h1>

        <motion.div
          variants={fadeInUp}
          transition={{ duration: 0.35, delay: 0.08 }}
          className="w-full max-w-[820px] px-4 pb-2 pt-3"
        >
          <div className="group relative">
            <div className="absolute -inset-px rounded-xl bg-[#155EEF]/40 opacity-35 blur-sm transition duration-500 group-hover:opacity-55" />
            <div className="relative rounded-xl bg-[#0A0A0B]/80 shadow-[0_14px_36px_rgba(0,0,0,0.28)] ring-1 ring-white/10 backdrop-blur-sm">
              <InputArea
                promptValue={promptValue}
                setPromptValue={setPromptValue}
                handleSubmit={handleDisplayResult}
              />
            </div>
          </div>

          <motion.div
            variants={fadeInUp}
            transition={{ duration: 0.35, delay: 0.12 }}
            className="mt-2 px-4 text-center"
          >
            {!hltBranding.enabled && (
              <p className="text-[11px] font-light leading-5 text-gray-500">
                GPT Researcher may make mistakes. Verify important information
                and check sources.
              </p>
            )}
          </motion.div>
        </motion.div>

        {hltBranding.enabled && (
          <motion.div
            variants={fadeInUp}
            transition={{ duration: 0.35, delay: 0.16 }}
            className="mt-3 w-full"
          >
            <ResearchScopeSelector
              value={chatBoxSettings?.hlt_research_scope}
              onChange={handleScopeChange}
            />
          </motion.div>
        )}

        {hltBranding.enabled && (
          <motion.div
            variants={fadeInUp}
            transition={{ duration: 0.35, delay: 0.2 }}
            className="mt-4 w-full max-w-[820px] px-4"
            aria-label="Example searches"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                Examples
              </span>
            </div>
            <div className="-mx-4 flex snap-x gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {exampleSearches.map((example) => (
                <button
                  key={example.label}
                  type="button"
                  title={example.query}
                  onClick={() => handleExampleSearch(example.query)}
                  className="group min-h-[72px] w-[190px] shrink-0 snap-start rounded-lg border border-white/10 bg-white/[0.035] px-3 py-2 text-left transition-colors hover:border-blue-400/40 hover:bg-white/[0.07] focus:outline-none focus:ring-2 focus:ring-blue-400/50"
                >
                  <span className="block text-xs font-semibold text-slate-200 group-hover:text-white">
                    {example.label}
                  </span>
                  <span className="mt-1 block text-[11px] leading-4 text-slate-500 group-hover:text-slate-300">
                    {example.description}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <div className="h-1" />
      </motion.div>
    </div>
  );
};

const exampleSearches = [
  {
    label: "AI trends",
    description: "Latest patterns for product, agents, and cleanup.",
    query:
      "Find current AI trends that could improve Katailyst workflows, frontend design, observability, and ecosystem cleanup.",
  },
  {
    label: "Frontend cleanup",
    description: "Find UI debt and design-system fixes.",
    query:
      "Map frontend cleanup opportunities across Katailyst-style product interfaces and suggest design-system enforcement patterns.",
  },
  {
    label: "QBank gaps",
    description: "Improve corporate CMS and question-bank quality.",
    query:
      "Research opportunities to improve corporate CMS and question-bank content quality using read-only internal context when available.",
  },
  {
    label: "Observability",
    description: "Trace runs, health checks, and drift.",
    query:
      "Research observability patterns for agent workflows, run traces, health checks, and ecosystem drift detection.",
  },
  {
    label: "Customer discovery",
    description: "Find audience pains and workflow signals.",
    query:
      "Research customer discovery themes, audience pains, objections, and workflow signals that could inform Katailyst product and content strategy.",
  },
];

export default Hero;
