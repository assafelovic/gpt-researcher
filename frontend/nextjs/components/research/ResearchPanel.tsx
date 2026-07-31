import React, { useState } from "react";
import { ResearchResults } from "@/components/ResearchResults";
import { Data, ChatBoxSettings } from "@/types/data";
import LoadingDots from "@/components/LoadingDots";
import Image from "next/image";

interface ResearchPanelProps {
  orderedData: Data[];
  answer: string;
  allLogs: any[];
  chatBoxSettings: ChatBoxSettings;
  handleClickSuggestion: (value: string) => void;
  currentResearchId?: string;
  onShareClick?: () => void;
  isCopilotVisible?: boolean;
  setIsCopilotVisible?: React.Dispatch<React.SetStateAction<boolean>>;
  onNewResearch?: () => void;
  loading?: boolean;
  toggleSidebar?: () => void;
}

const ResearchPanel: React.FC<ResearchPanelProps> = ({
  orderedData,
  answer,
  allLogs,
  chatBoxSettings,
  handleClickSuggestion,
  currentResearchId,
  onShareClick,
  isCopilotVisible,
  setIsCopilotVisible,
  onNewResearch,
  loading,
  toggleSidebar,
}) => {
  // Determine if research is complete (has answer) and copilot should be highlighted
  const researchComplete = Boolean(answer && answer.length > 0);
  const [isNotificationDismissed, setIsNotificationDismissed] = useState(false);

  return (
    <>
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-gray-800/60 bg-gray-900/40 px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-teal-300 shadow-[0_0_18px_rgba(45,212,191,0.55)]" />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">
              {researchComplete ? "Research report" : "Research run"}
            </p>
            <p className="hidden text-xs text-slate-400 sm:block">
              {researchComplete
                ? "Report first. Activity logs stay available below."
                : "Live activity will stack as the run progresses."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* New Research button */}
          {onNewResearch && (
            <button
              onClick={onNewResearch}
              className="flex items-center gap-1.5 rounded-md bg-sky-200/80 px-3 py-1.5 text-sm font-medium text-sky-800 transition-colors hover:bg-sky-300/80"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              New Research
            </button>
          )}

          {/* Share button */}
          {onShareClick && currentResearchId && (
            <button
              onClick={onShareClick}
              className="flex items-center gap-1.5 rounded-md border border-teal-500/50 bg-teal-600 px-3 py-1.5 text-sm text-white shadow-sm transition-colors hover:bg-teal-700 hover:shadow-teal-500/20"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path>
                <polyline points="16 6 12 2 8 6"></polyline>
                <line x1="12" y1="2" x2="12" y2="15"></line>
              </svg>
              Share
            </button>
          )}

          {/* Show Copilot button - only visible when copilot is hidden */}
          {!isCopilotVisible && setIsCopilotVisible && (
            <button
              onClick={() => setIsCopilotVisible(true)}
              className={`flex items-center gap-1.5 rounded-md border border-teal-700/60 bg-teal-800/70 px-3 py-1.5 text-sm text-teal-100 transition-colors hover:bg-teal-700 ${researchComplete ? "animate-chat-button-pulse" : ""}`}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              Chat
            </button>
          )}
        </div>
      </div>

      <div className="custom-scrollbar flex-1 overflow-y-auto bg-gray-900/20 p-3">
        {/* Filter out chat messages so they only show in the chat panel */}
        <div className="relative space-y-4">
          <ResearchResults
            orderedData={orderedData.filter((data) => {
              // Keep everything except chat responses
              if (data.type === "chat") return false;

              // For questions, only keep the first/initial question
              if (data.type === "question") {
                return orderedData.indexOf(data) === 0;
              }

              // Keep all other types
              return true;
            })}
            answer={answer}
            allLogs={allLogs}
            chatBoxSettings={chatBoxSettings}
            handleClickSuggestion={handleClickSuggestion}
            currentResearchId={currentResearchId}
            loading={loading}
          />

          {/* Loading indicator - show during research */}
          {loading && (
            <div className="mt-6 flex justify-center">
              <div className="flex flex-col items-center">
                <LoadingDots />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Custom scrollbar styles */}
      <style jsx global>{`
        @keyframes chat-button-pulse {
          0%,
          100% {
            box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.4);
            transform: scale(1);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(20, 184, 166, 0);
            transform: scale(1.02);
          }
        }

        .animate-chat-button-pulse {
          animation: chat-button-pulse 2s infinite cubic-bezier(0.66, 0, 0, 1);
        }

        @keyframes fade-in-up {
          0% {
            opacity: 0;
            transform: translateY(10px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in-up {
          animation: fade-in-up 0.6s ease-out forwards;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(17, 24, 39, 0.1);
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(75, 85, 99, 0.5);
          border-radius: 20px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(75, 85, 99, 0.7);
        }
      `}</style>
    </>
  );
};

export default ResearchPanel;
