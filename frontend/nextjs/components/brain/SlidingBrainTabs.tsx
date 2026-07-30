"use client";

import { motion } from "framer-motion";
import { BRAIN_TABS, BrainTabId } from "@/lib/brainTabs";

type Props = {
  active: BrainTabId;
  onChange: (id: BrainTabId) => void;
};

/**
 * Sliding glow tabs for Mastery Brain surfaces.
 * Inspired by @ruixen.ui/sliding-tabs (21st registry) — inlined because
 * API_KEY_21ST was not available in this environment.
 */
export default function SlidingBrainTabs({ active, onChange }: Props) {
  return (
    <div className="relative mx-auto w-full max-w-4xl px-4">
      <div
        role="tablist"
        aria-label="Mastery Brain"
        className="relative flex flex-wrap items-center justify-center gap-1 rounded-2xl border border-white/10 bg-white/[0.03] p-1.5 backdrop-blur-md"
      >
        {BRAIN_TABS.map((tab) => {
          const isActive = tab.id === active;
          return (
            <button
              key={tab.id}
              role="tab"
              type="button"
              aria-selected={isActive}
              title={tab.description}
              onClick={() => onChange(tab.id)}
              className={`relative z-10 rounded-xl px-3.5 py-2 text-sm font-medium transition-colors sm:px-4 ${
                isActive ? "text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {isActive && (
                <motion.span
                  layoutId="brain-tab-glow"
                  className="absolute inset-0 -z-10 rounded-xl bg-gradient-to-r from-teal-500/30 via-cyan-400/25 to-sky-500/30 shadow-[0_0_24px_rgba(45,212,191,0.25)]"
                  transition={{ type: "spring", stiffness: 380, damping: 32 }}
                />
              )}
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
