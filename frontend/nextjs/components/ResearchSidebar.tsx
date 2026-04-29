import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { ResearchHistoryItem } from "../types/data";
import { formatDistanceToNow } from "date-fns";
import { motion, AnimatePresence } from "framer-motion";

interface ResearchSidebarProps {
  history: ResearchHistoryItem[];
  onSelectResearch: (id: string) => void;
  onNewResearch: () => void;
  onDeleteResearch: (id: string) => void;
  isOpen: boolean;
  toggleSidebar: () => void;
}

const ResearchSidebar: React.FC<ResearchSidebarProps> = ({
  history,
  onSelectResearch,
  onNewResearch,
  onDeleteResearch,
  isOpen,
  toggleSidebar,
}) => {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isOpen &&
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target as Node)
      ) {
        toggleSidebar();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, toggleSidebar]);

  // Format timestamp for display
  const formatTimestamp = (timestamp: number | string | Date | undefined) => {
    if (!timestamp) return "Unknown time";

    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return "Unknown time";
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return "Unknown time";
    }
  };

  // Animation variants
  const sidebarVariants = {
    open: {
      width: "var(--sidebar-width)",
      transition: { type: "spring", stiffness: 250, damping: 25 },
    },
    closed: {
      width: "var(--sidebar-min-width)",
      transition: { type: "spring", stiffness: 250, damping: 25, delay: 0.1 },
    },
  };

  const fadeInVariants = {
    hidden: { opacity: 0, transition: { duration: 0.2 } },
    visible: { opacity: 1, transition: { duration: 0.3 } },
  };

  return (
    <>
      {/* Overlay for mobile */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="sidebar-overlay fixed inset-0 z-40 bg-black bg-opacity-50 backdrop-blur-sm md:hidden"
            onClick={toggleSidebar}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      <motion.div
        ref={sidebarRef}
        className="sidebar-z-index fixed left-0 top-0 h-full"
        variants={sidebarVariants}
        initial={false}
        animate={isOpen ? "open" : "closed"}
        style={
          {
            "--sidebar-width": "min(300px, 85vw)",
            "--sidebar-min-width": "12px",
          } as React.CSSProperties
        }
      >
        {/* Sidebar content */}
        <div
          className={`h-full overflow-hidden text-white transition-all duration-300 ${
            isOpen
              ? "bg-gray-900/80 p-3 shadow-2xl shadow-black/30 backdrop-blur-md sm:p-4"
              : "bg-transparent p-0"
          }`}
        >
          {/* Toggle button - only shown when sidebar is closed */}
          <AnimatePresence mode="wait">
            {!isOpen ? (
              <motion.div
                key="toggle-button"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="absolute left-4 top-2 z-10 flex h-6 cursor-pointer items-center justify-center rounded border border-white/10 bg-white/[0.025] px-2 text-[10px] font-medium text-slate-500 transition-colors hover:border-white/20 hover:text-slate-300 sm:left-6"
                onClick={toggleSidebar}
                aria-label="Open sidebar"
              >
                History
              </motion.div>
            ) : (
              <motion.div
                key="sidebar-content"
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={fadeInVariants}
              >
                <div className="mb-5 flex items-center justify-between sm:mb-6">
                  <h2 className="bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-lg font-semibold text-transparent sm:text-xl">
                    Research History
                  </h2>
                  <button
                    onClick={toggleSidebar}
                    className="group flex h-8 w-8 items-center justify-center rounded-full bg-gray-800/60 text-white shadow-lg transition-all duration-300 hover:bg-gray-800 sm:h-10 sm:w-10"
                    aria-label="Close sidebar"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 transition-transform duration-300 group-hover:scale-110"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                  </button>
                </div>

                {/* New Research button */}
                <button
                  onClick={onNewResearch}
                  className="group relative mb-5 w-full overflow-hidden rounded-md bg-teal-500 px-3 py-2.5 text-sm font-bold text-white transition-all duration-300 sm:mb-6 sm:px-4 sm:py-3"
                >
                  {/* Gradient background on hover */}
                  <div className="absolute inset-0 bg-gradient-to-br from-[#0cdbb6] via-[#1fd0f0] to-[#06dbee] opacity-0 transition-opacity duration-500 group-hover:opacity-100"></div>

                  {/* Magical glow effect */}
                  <div
                    className="absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                    style={{
                      boxShadow: "inset 0 0 20px 5px rgba(255, 255, 255, 0.2)",
                      background:
                        "radial-gradient(circle at center, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0) 70%)",
                    }}
                  ></div>

                  <div className="relative z-10 flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="mr-2 h-4 w-4 transition-transform duration-300 group-hover:scale-110 sm:h-5 sm:w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                    New Research
                  </div>
                </button>

                {/* History list with improved scrollbar */}
                <div className="custom-scrollbar h-[calc(100vh-150px)] overflow-y-auto pr-1 sm:h-[calc(100vh-190px)]">
                  {history.length === 0 ? (
                    <div className="px-4 py-8 text-center sm:py-10">
                      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-gray-800/60 to-gray-700/40 sm:h-20 sm:w-20">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-8 w-8 text-gray-500 sm:h-10 sm:w-10"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                      </div>
                      <h3 className="mb-2 text-lg font-medium text-gray-300">
                        No research history yet
                      </h3>
                      <p className="text-sm text-gray-400">
                        Start a research run to save reports here.
                      </p>
                    </div>
                  ) : (
                    <ul className="space-y-2 sm:space-y-3">
                      {history.map((item) => (
                        <motion.li
                          key={item.id}
                          className="group relative overflow-hidden rounded-xl border border-gray-700/30 bg-gray-900/40 backdrop-blur-sm transition-all duration-300 hover:border-gray-600/50 hover:bg-gray-800/60"
                          onMouseEnter={() => setHoveredItem(item.id)}
                          onMouseLeave={() => setHoveredItem(null)}
                        >
                          <Link
                            href={`/research/${item.id}`}
                            className="relative block min-h-[56px] w-full p-3 pr-10 text-left sm:p-4"
                            onClick={(e) => {
                              // Only prevent default if we're just closing the sidebar
                              if (!isOpen) {
                                e.preventDefault();
                              }
                              // Call onSelectResearch only if we're actually navigating
                              if (isOpen) {
                                onSelectResearch(item.id);
                              }
                              // Always close the sidebar
                              toggleSidebar();
                            }}
                          >
                            <h3 className="truncate text-sm font-medium text-gray-200 transition-colors duration-200 group-hover:text-teal-400 sm:text-base">
                              {item.question}
                            </h3>
                            <p className="mt-1.5 flex items-center text-xs text-gray-400">
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className="mr-1 h-3.5 w-3.5 text-gray-500"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                              </svg>
                              {formatTimestamp(
                                item.timestamp ||
                                  (item as any).updated_at ||
                                  (item as any).created_at,
                              )}
                            </p>
                          </Link>

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteResearch(item.id);
                            }}
                            className="absolute right-2 top-2 rounded-full p-1.5 text-gray-400 opacity-0 transition-opacity hover:bg-gray-700 hover:text-white group-hover:opacity-100"
                            aria-label="Delete research"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-4 w-4"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                              />
                            </svg>
                          </button>
                        </motion.li>
                      ))}
                    </ul>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Custom scrollbar styles */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.3);
          border-radius: 20px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(45, 212, 191, 0.3);
          border-radius: 20px;
          transition: all 0.3s;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(45, 212, 191, 0.6);
        }
      `}</style>
    </>
  );
};

export default ResearchSidebar;
