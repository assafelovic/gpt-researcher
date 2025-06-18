import React from "react";
import Image from "next/image";
import { motion } from "framer-motion";

interface HeaderProps {
  loading?: boolean;      // Indicates if research is currently in progress
  isStopped?: boolean;    // Indicates if research was manually stopped
  showResult?: boolean;   // Controls if research results are being displayed
  onNewResearch?: () => void;  // Handler for starting fresh research
  connectionStatus?: string; // Current connection status
  isRetrying?: boolean;   // Whether the system is retrying connection
}

const Header = ({ loading, isStopped, showResult, onNewResearch, connectionStatus, isRetrying }: HeaderProps) => {
  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Pure transparent blur background */}
      <div className="absolute inset-0 backdrop-blur-sm bg-transparent"></div>
      {/* Header container */}
      <div className="container relative h-[60px] px-4 lg:h-[80px] lg:px-0 pt-4 pb-4">
        <div className="flex flex-col items-center">
          {/* Logo/Home link */}
          <a href="/">
            <img
              src="/img/gptr-logo.png"
              alt="logo"
              width={60}
              height={60}
              className="lg:h-16 lg:w-16"
            />
          </a>

          {/* Action buttons container */}
          <div className="flex gap-2 mt-2 transition-all duration-300 ease-in-out">
            {/* Connection status indicator - subtle and unobtrusive */}
            {isRetrying && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-1 px-3 h-9 sm:h-10 text-xs text-orange-400 bg-orange-900/20 rounded-full border border-orange-500/30"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="w-3 h-3"
                >
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </motion.div>
                <span className="hidden sm:inline">Reconnecting</span>
              </motion.div>
            )}

            {/* New Research button - shown after stopping or completing research */}
            {(isStopped || !loading) && showResult && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={onNewResearch}
                className="flex items-center justify-center px-4 sm:px-6 h-9 sm:h-10 text-sm text-white bg-purple-500 rounded-full hover:bg-purple-600 transform hover:scale-105 transition-all duration-200 shadow-lg whitespace-nowrap min-w-[120px]"
              >
                New Research
              </motion.button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
