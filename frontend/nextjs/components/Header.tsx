import React from 'react';
import Link from "next/link";
import MasteryIcon from "@/components/MasteryIcon";
import { hltBranding } from "@/lib/hltBranding";

interface HeaderProps {
  loading?: boolean;      // Indicates if research is currently in progress
  isStopped?: boolean;    // Indicates if research was manually stopped
  showResult?: boolean;   // Controls if research results are being displayed
  onStop?: () => void;    // Handler for stopping ongoing research
  onNewResearch?: () => void;  // Handler for starting fresh research
  isCopilotMode?: boolean; // Indicates if we are in copilot mode
}

const Header = ({ loading, isStopped, showResult, onStop, onNewResearch, isCopilotMode }: HeaderProps) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      <div className="absolute inset-0 border-b border-white/10 bg-[#06101C]/82 backdrop-blur-xl"></div>

      <div className="container relative flex min-h-[72px] items-center justify-between gap-4 px-4 lg:px-0">
        <Link href="/" className="flex min-w-0 items-center gap-3">
          {hltBranding.enabled ? (
            <MasteryIcon size={42} className="shrink-0" />
          ) : (
            <img
              src="/img/gptr-logo.png"
              alt="GPT Researcher"
              width={44}
              height={44}
              className="h-11 w-11 shrink-0"
            />
          )}
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold tracking-[0.08em] text-white sm:text-base">
              {hltBranding.enabled ? hltBranding.productName : "GPT Researcher"}
            </div>
            <div className="hidden text-xs text-slate-300 sm:block">
              {hltBranding.enabled ? hltBranding.subtitle : "Autonomous research agent"}
            </div>
          </div>
        </Link>

        <div className="flex items-center gap-2">
          {hltBranding.enabled && (
            <a
              href={hltBranding.katailystUrl}
              target="_blank"
              rel="noreferrer"
              className="hidden h-9 items-center rounded-md border border-white/10 px-3 text-sm font-medium text-slate-200 transition-colors hover:border-white/25 hover:text-white sm:flex"
            >
              Open {hltBranding.platformName}
            </a>
          )}
          <div className="flex gap-2 transition-all duration-300 ease-in-out">
            {/* Stop button - shown only during active research */}
            {loading && !isStopped && (
              <button
                onClick={onStop}
                className="flex h-9 min-w-[72px] items-center justify-center rounded-md bg-red-500 px-4 text-sm font-medium text-white shadow-lg transition-all duration-200 hover:bg-red-600 sm:px-5"
              >
                Stop
              </button>
            )}
            {/* New Research button - shown after stopping or completing research - but not in copilot mode */}
            {(isStopped || !loading) && showResult && !isCopilotMode && (
              <button
                onClick={onNewResearch}
                className="flex h-9 min-w-[112px] items-center justify-center rounded-md bg-[#155EEF] px-4 text-sm font-semibold text-white shadow-lg shadow-blue-950/25 transition-all duration-200 hover:bg-[#0E49C9] sm:px-5"
              >
                New Research
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
