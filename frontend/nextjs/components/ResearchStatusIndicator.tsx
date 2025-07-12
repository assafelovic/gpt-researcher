import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ConnectionStatus, ResearchState } from '../hooks/useConnectionManager';
import { ConnectionHealth } from '../hooks/useConnectionHealth';

interface ResearchStatusIndicatorProps {
  researchState: ResearchState;
  getStatusDescription: (status: ConnectionStatus) => string;
  isVisible: boolean;
  connectionHealth?: ConnectionHealth;
  getHealthDescription?: (quality: ConnectionHealth["quality"]) => string;
  getHealthColor?: (quality: ConnectionHealth["quality"]) => string;
}

const ResearchStatusIndicator: React.FC<ResearchStatusIndicatorProps> = ({
  researchState,
  getStatusDescription,
  isVisible,
  connectionHealth,
  getHealthDescription,
  getHealthColor
}) => {
  const { status, progress, currentTask, isRetrying, retryCount } = researchState;
  const [isDismissed, setIsDismissed] = useState(false);

  // Reset dismissed state when a new research starts
  React.useEffect(() => {
    if (status === "preparing" || status === "connecting") {
      setIsDismissed(false);
    }
  }, [status]);

  // Get status color based on current state
  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case "idle":
        return "text-gray-400";
      case "preparing":
        return "text-blue-400";
      case "connecting":
        return "text-yellow-400";
      case "connected":
        return "text-green-400";
      case "processing":
        return "text-teal-400";
      case "completed":
        return "text-green-500";
      case "reconnecting":
        return "text-orange-400";
      case "recovering":
        return "text-purple-400";
      default:
        return "text-gray-400";
    }
  };

  // Get status icon based on current state
  const getStatusIcon = (status: ConnectionStatus) => {
    switch (status) {
      case "idle":
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case "preparing":
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
          </svg>
        );
      case "connecting":
      case "reconnecting":
        return (
          <motion.svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </motion.svg>
        );
      case "connected":
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
          </svg>
        );
      case "processing":
        return (
          <motion.svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </motion.svg>
        );
      case "completed":
        return (
          <motion.svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 500, damping: 30 }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </motion.svg>
        );
      case "recovering":
        return (
          <motion.svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            animate={{ x: [0, 2, 0] }}
            transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </motion.svg>
        );
      default:
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  // Progress bar component
  const ProgressBar = () => (
    <div className="w-full bg-gray-700/30 rounded-full h-1 overflow-hidden">
      <motion.div
        className="h-full bg-gradient-to-r from-teal-500 to-cyan-400 rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${progress}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </div>
  );

  // Retry indicator
  const RetryIndicator = () => (
    isRetrying && retryCount > 0 && (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center gap-1 text-xs text-orange-400"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-2 h-2"
        >
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </motion.div>
        <span className="text-xs">{retryCount}</span>
      </motion.div>
    )
  );

  // Don't show if dismissed or not visible
  if (isDismissed || !isVisible) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="fixed top-4 right-4 z-40"
      >
        <div className="bg-gray-900/95 backdrop-blur-md border border-gray-700/50 rounded-lg shadow-lg px-3 py-2 min-w-[200px] max-w-[280px]">
          {/* Status header with dismiss button */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <div className={`${getStatusColor(status)} flex-shrink-0`}>
                {getStatusIcon(status)}
              </div>
              <span className={`text-xs font-medium ${getStatusColor(status)} truncate`}>
                {getStatusDescription(status)}
              </span>
              <RetryIndicator />
            </div>
            <button
              onClick={() => setIsDismissed(true)}
              className="ml-2 text-gray-400 hover:text-gray-200 transition-colors flex-shrink-0"
              aria-label="Dismiss status"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Current task */}
          {currentTask && currentTask !== getStatusDescription(status) && (
            <div className="text-xs text-gray-400 mt-1 truncate">
              {currentTask}
            </div>
          )}

          {/* Progress bar */}
          {(status === "processing" || status === "recovering") && progress > 0 && (
            <div className="mt-2 space-y-1">
              <ProgressBar />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
            </div>
          )}

          {/* Connection quality indicator - compact version */}
          {status === "connected" && connectionHealth && getHealthDescription && getHealthColor && (
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center gap-1">
                <div className="flex gap-0.5">
                  {[1, 2, 3].map((bar) => {
                    const opacity =
                      connectionHealth.quality === "excellent"
                        ? 1
                        : connectionHealth.quality === "good"
                          ? bar <= 2
                            ? 1
                            : 0.3
                          : connectionHealth.quality === "fair"
                            ? bar <= 1
                              ? 1
                              : 0.3
                            : 0.3;
                    return (
                      <div
                        key={bar}
                        className={`w-0.5 rounded-full ${getHealthColor(connectionHealth.quality).replace("text-", "bg-")}`}
                        style={{ height: `${bar * 2 + 2}px`, opacity }}
                      />
                    );
                  })}
                </div>
                <span className={`text-xs ${getHealthColor(connectionHealth.quality)}`}>
                  {connectionHealth.latency}ms
                </span>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ResearchStatusIndicator;
