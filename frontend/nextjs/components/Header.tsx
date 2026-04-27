import React from "react";
import Link from "next/link";
import MasteryIcon from "@/components/MasteryIcon";
import { hltBranding } from "@/lib/hltBranding";
import Modal from "@/components/Settings/Modal";
import { ChatBoxSettings } from "@/types/data";

interface HeaderProps {
  loading?: boolean; // Indicates if research is currently in progress
  isStopped?: boolean; // Indicates if research was manually stopped
  showResult?: boolean; // Controls if research results are being displayed
  onStop?: () => void; // Handler for stopping ongoing research
  onNewResearch?: () => void; // Handler for starting fresh research
  isCopilotMode?: boolean; // Indicates if we are in copilot mode
  chatBoxSettings?: ChatBoxSettings;
  setChatBoxSettings?: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
}

const Header = ({
  loading,
  isStopped,
  showResult,
  onStop,
  onNewResearch,
  isCopilotMode,
  chatBoxSettings,
  setChatBoxSettings,
}: HeaderProps) => {
  return (
    <header className="fixed left-0 right-0 top-0 z-50">
      <div className="bg-[#06101C]/82 absolute inset-0 border-b border-white/10 backdrop-blur-xl"></div>

      <div className="container relative flex min-h-[48px] items-center justify-between gap-3 px-4 lg:px-0">
        <Link
          href="/"
          className="flex min-w-0 items-center gap-2"
          aria-label={
            hltBranding.enabled ? hltBranding.productName : "GPT Researcher"
          }
          title={
            hltBranding.enabled ? hltBranding.productName : "GPT Researcher"
          }
        >
          {hltBranding.enabled ? (
            <MasteryIcon size={30} className="shrink-0" />
          ) : (
            <img
              src="/img/gptr-logo.png"
              alt="GPT Researcher"
              width={44}
              height={44}
              className="h-7 w-7 shrink-0"
            />
          )}
        </Link>

        <div className="flex items-center gap-2">
          {chatBoxSettings && setChatBoxSettings ? (
            <Modal
              chatBoxSettings={chatBoxSettings}
              setChatBoxSettings={setChatBoxSettings}
            />
          ) : null}
          {hltBranding.enabled && (
            <a
              href={hltBranding.katailystUrl}
              target="_blank"
              rel="noreferrer"
              className="hidden h-7 items-center rounded-md border border-white/10 px-2.5 text-[11px] font-medium text-slate-400 transition-colors hover:border-white/25 hover:text-white sm:flex"
            >
              Open {hltBranding.platformName}
            </a>
          )}
          <div className="flex gap-2 transition-all duration-300 ease-in-out">
            {/* Stop button - shown only during active research */}
            {loading && !isStopped && (
              <button
                onClick={onStop}
                className="flex h-8 min-w-[68px] items-center justify-center rounded-md bg-red-500 px-3 text-xs font-medium text-white shadow-lg transition-all duration-200 hover:bg-red-600"
              >
                Stop
              </button>
            )}
            {/* New Research button - shown after stopping or completing research - but not in copilot mode */}
            {(isStopped || !loading) && showResult && !isCopilotMode && (
              <button
                onClick={onNewResearch}
                className="flex h-8 min-w-[104px] items-center justify-center rounded-md bg-[#155EEF] px-3 text-xs font-semibold text-white shadow-lg shadow-blue-950/25 transition-all duration-200 hover:bg-[#0E49C9]"
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
