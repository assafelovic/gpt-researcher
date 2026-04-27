import React, { useState, useEffect, useRef, useCallback } from "react";
import { ResearchHistoryItem } from "@/types/data";
import { useResearchHistoryContext } from "@/hooks/ResearchHistoryContext";
import LoadingDots from "@/components/LoadingDots";
import { toast } from "react-hot-toast";
import MasteryIcon from "@/components/MasteryIcon";
import { hltBranding } from "@/lib/hltBranding";

interface MobileHomeScreenProps {
  promptValue: string;
  setPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleDisplayResult: (newQuestion: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
  handleKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
}

export default function MobileHomeScreen({
  promptValue,
  setPromptValue,
  handleDisplayResult,
  isLoading = false,
  placeholder = "What would you like to research today?",
  handleKeyDown,
}: MobileHomeScreenProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { history } = useResearchHistoryContext();
  const [recentHistory, setRecentHistory] = useState<ResearchHistoryItem[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submissionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get recent research history
  useEffect(() => {
    // Get the 3 most recent items
    if (history && history.length > 0) {
      setRecentHistory(history.slice(0, 3));
    }
  }, [history]);

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        textareaRef.current.scrollHeight + "px";
    }
  }, [promptValue]);

  // Clean up any timeouts on unmount
  useEffect(() => {
    return () => {
      if (submissionTimeoutRef.current) {
        clearTimeout(submissionTimeoutRef.current);
      }
    };
  }, []);

  // Handle history item click
  const handleHistoryItemClick = useCallback((id: string) => {
    window.location.href = `/research/${id}`;
  }, []);

  const handlePromptChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setPromptValue(e.target.value);
    },
    [setPromptValue],
  );

  const handleSubmit = useCallback(async () => {
    // Don't submit if empty, already loading, or already submitting
    if (!promptValue.trim() || isLoading || isSubmitting) {
      return;
    }

    try {
      // Set submitting state for UI feedback
      setIsSubmitting(true);

      // Add a timeout as a safety measure to prevent infinite loading
      submissionTimeoutRef.current = setTimeout(() => {
        setIsSubmitting(false);
        toast.error("Research request took too long. Please try again.", {
          duration: 3000,
          position: "bottom-center",
        });
      }, 15000); // 15 second timeout

      // Create a new simplified direct API submission that won't use websockets
      try {
        // First show visual feedback
        const trimmedPrompt = promptValue.trim();

        // Call the display result handler from props
        await handleDisplayResult(trimmedPrompt);

        // Clear the timeout since we successfully completed
        if (submissionTimeoutRef.current) {
          clearTimeout(submissionTimeoutRef.current);
          submissionTimeoutRef.current = null;
        }
      } catch (apiError) {
        console.error("API error during research submission:", apiError);
        toast.error(
          "There was a problem submitting your research. Please try again.",
          {
            duration: 3000,
            position: "bottom-center",
          },
        );

        // Clear submission state
        setIsSubmitting(false);
      }
    } catch (error) {
      console.error("Error during research submission:", error);
      // Reset state in case of error
      setIsSubmitting(false);

      // Clear any existing timeout
      if (submissionTimeoutRef.current) {
        clearTimeout(submissionTimeoutRef.current);
        submissionTimeoutRef.current = null;
      }
    }
  }, [promptValue, isLoading, isSubmitting, handleDisplayResult]);

  // Handle enter key for submission
  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (handleKeyDown) {
        handleKeyDown(e);
      }

      // Submit on Enter (without shift)
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleKeyDown, handleSubmit],
  );

  return (
    <div className="flex h-full w-full flex-col bg-gradient-to-b from-gray-900 to-gray-950 pb-16">
      {/* Header with logo and title */}
      <div className="mb-5 px-6 pt-6 text-center">
        <div className="mb-2 flex justify-center">
          {hltBranding.enabled ? (
            <MasteryIcon size={48} />
          ) : (
            <img
              src="/img/gptr-logo.png"
              alt="GPT Researcher"
              width={60}
              height={60}
              className="h-12 w-12 rounded-xl"
            />
          )}
        </div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-blue-300">
          {hltBranding.enabled ? hltBranding.productName : "GPT Researcher"}
        </p>
        <p className="mx-auto mt-1 max-w-[280px] text-xs leading-5 text-gray-500">
          {hltBranding.enabled
            ? "Source-backed research for the HLT agent stack."
            : "Say Hello to GPT Researcher, your AI partner for instant insights and comprehensive research"}
        </p>
      </div>

      {/* Search Box */}
      <div className="mx-auto w-full max-w-lg px-4 md:px-8">
        <div
          className={`relative rounded-xl border bg-gray-800 shadow-lg transition-all duration-300 ${isFocused ? "input-glow-active border-sky-500/70" : "input-glow-subtle border-gray-700/50"}`}
        >
          <textarea
            ref={textareaRef}
            className="w-full resize-none rounded-xl bg-transparent px-4 pb-11 pt-4 text-sm leading-6 text-gray-200 focus:outline-none"
            placeholder={placeholder}
            value={promptValue}
            onChange={handlePromptChange}
            onKeyDown={handleKeyPress}
            rows={1}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            disabled={isLoading || isSubmitting}
          />

          <div className="absolute bottom-2.5 right-2.5">
            <button
              onClick={handleSubmit}
              disabled={isLoading || isSubmitting || !promptValue.trim()}
              className={`rounded-full p-2 ${
                isLoading || isSubmitting || !promptValue.trim()
                  ? "bg-gray-700 text-gray-500"
                  : "bg-sky-600 text-white hover:bg-sky-500"
              } transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-opacity-50`}
              aria-label="Start research"
            >
              {isLoading || isSubmitting ? (
                <div className="flex items-center justify-center">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600"></div>
                </div>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              )}
            </button>
          </div>
        </div>
        <p className="mt-2 px-2 text-center text-xs text-gray-500">
          Enter any research topic or specific question
        </p>
      </div>

      <div className="mx-auto mt-4 flex w-full max-w-lg flex-wrap justify-center gap-2 px-4">
        {[
          "AI trends for Katailyst",
          "Frontend cleanup map",
          "Observability patterns",
        ].map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => setPromptValue(suggestion)}
            className="rounded-md border border-gray-700/70 bg-gray-800/50 px-3 py-1.5 text-xs text-gray-300"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {/* Recent research history */}
      {recentHistory.length > 0 && (
        <div className="mt-7 px-4">
          <h2 className="mb-3 px-2 text-sm font-medium text-gray-400">
            Recent Research
          </h2>
          <div className="space-y-2">
            {recentHistory.map((item) => (
              <button
                key={item.id}
                onClick={() => handleHistoryItemClick(item.id)}
                className="w-full rounded-lg bg-gray-800/60 p-3 text-left transition-colors hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-600"
              >
                <h3 className="line-clamp-1 text-sm font-medium text-gray-200">
                  {item.question}
                </h3>
                <p className="mt-1 text-xs text-gray-500">
                  {new Date(item.timestamp || Date.now()).toLocaleString()}
                </p>
              </button>
            ))}
          </div>
          <div className="mt-3 text-center">
            <a
              href="/history"
              className="inline-block text-sm text-sky-400 transition-colors hover:text-sky-300"
            >
              View all research
            </a>
          </div>
        </div>
      )}

      {/* Features or tips section */}
      <div className="mt-auto px-4 pb-4 pt-6">
        <div className="rounded-xl border border-gray-800/70 bg-gray-900/40 p-3 text-center">
          <p className="text-xs leading-5 text-gray-500">
            Reports are source-backed. Use specific questions, dates, and
            context for deeper runs.
          </p>
        </div>
      </div>

      {/* Styling for line clamp and input glow */}
      <style jsx global>{`
        .line-clamp-1 {
          overflow: hidden;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
        }

        .input-glow-subtle {
          box-shadow:
            0 0 5px rgba(56, 189, 248, 0.2),
            0 0 12px rgba(14, 165, 233, 0.15),
            0 0 20px rgba(2, 132, 199, 0.1);
          animation: pulse-glow-subtle 3s infinite alternate;
        }

        @keyframes pulse-glow-subtle {
          0% {
            box-shadow:
              0 0 5px rgba(56, 189, 248, 0.2),
              0 0 12px rgba(14, 165, 233, 0.15),
              0 0 20px rgba(2, 132, 199, 0.1);
          }
          100% {
            box-shadow:
              0 0 8px rgba(56, 189, 248, 0.25),
              0 0 15px rgba(14, 165, 233, 0.2),
              0 0 25px rgba(2, 132, 199, 0.15);
          }
        }

        .input-glow-active {
          box-shadow:
            0 0 5px rgba(56, 189, 248, 0.3),
            0 0 15px rgba(56, 189, 248, 0.3),
            0 0 25px rgba(14, 165, 233, 0.2),
            inset 0 0 3px rgba(186, 230, 253, 0.1);
          animation: pulse-glow-active 2s infinite alternate;
        }

        @keyframes pulse-glow-active {
          0% {
            box-shadow:
              0 0 5px rgba(56, 189, 248, 0.3),
              0 0 15px rgba(56, 189, 248, 0.3),
              0 0 25px rgba(14, 165, 233, 0.2),
              inset 0 0 3px rgba(186, 230, 253, 0.1);
          }
          100% {
            box-shadow:
              0 0 8px rgba(56, 189, 248, 0.4),
              0 0 20px rgba(14, 165, 233, 0.4),
              0 0 30px rgba(2, 132, 199, 0.3),
              inset 0 0 5px rgba(186, 230, 253, 0.2);
          }
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
