import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ConnectionStatus,
  ResilientConnectionState,
  ConnectionQuality,
} from "../hooks/useResilientConnection";

interface ResilientConnectionStatusProps {
  connectionState: ResilientConnectionState;
  className?: string;
  position?:
  | "top-left"
  | "top-right"
  | "top-center"
  | "bottom-left"
  | "bottom-right"
  | "bottom-center";
  showMetrics?: boolean;
  compactMode?: boolean;
}

const ResilientConnectionStatus: React.FC<ResilientConnectionStatusProps> = ({
  connectionState,
  className = "",
  position = "top-center",
  showMetrics = false,
  compactMode = false,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [autoHideTimeout, setAutoHideTimeout] = useState<number | null>(null);
  const [lastShownLevel, setLastShownLevel] = useState<string>("none");

  const {
    status,
    quality,
    progress,
    currentTask,
    isRetrying,
    retryCount,
    totalRetries,
    context,
    userFeedbackLevel,
    uptime,
    requestsInFlight,
    queuedRequests,
    backgroundActivity,
  } = connectionState;

  // Determine if status should be shown based on feedback level
  const shouldShowStatus = useCallback(() => {
    switch (userFeedbackLevel) {
      case "none":
        return false;
      case "minimal":
        return (
          status === "reconnecting" ||
          status === "failed" ||
          (isRetrying && retryCount > 2)
        );
      case "contextual":
        return (
          status !== "idle" &&
          status !== "ready" &&
          status !== "connected"
        );
      case "detailed":
        return true;
      default:
        return false;
    }
  }, [userFeedbackLevel, status, isRetrying, retryCount]);

  // Auto-hide logic for successful connections
  useEffect(() => {
    const shouldShow = shouldShowStatus();

    if (shouldShow && !isVisible) {
      setIsVisible(true);
      setLastShownLevel(userFeedbackLevel);

      // Clear any existing auto-hide timeout
      if (autoHideTimeout) {
        clearTimeout(autoHideTimeout);
        setAutoHideTimeout(null);
      }
    } else if (!shouldShow && isVisible) {
      // Auto-hide after successful connection
      if (status === "ready" || status === "connected") {
        const timeout = window.setTimeout(() => {
          setIsVisible(false);
          setAutoHideTimeout(null);
        }, 2000); // Hide after 2 seconds

        setAutoHideTimeout(timeout);
      } else {
        setIsVisible(false);
      }
    }

    return () => {
      if (autoHideTimeout) {
        clearTimeout(autoHideTimeout);
      }
    };
  }, [
    shouldShowStatus,
    isVisible,
    status,
    userFeedbackLevel,
    autoHideTimeout,
  ]);

  // Get position classes
  const getPositionClasses = () => {
    switch (position) {
      case "top-left":
        return "top-4 left-4";
      case "top-right":
        return "top-4 right-4";
      case "top-center":
        return "top-4 left-1/2 transform -translate-x-1/2";
      case "bottom-left":
        return "bottom-4 left-4";
      case "bottom-right":
        return "bottom-4 right-4";
      case "bottom-center":
        return "bottom-4 left-1/2 transform -translate-x-1/2";
      default:
        return "top-4 left-1/2 transform -translate-x-1/2";
    }
  };

  // Get status color and styling
  const getStatusStyling = (
    status: ConnectionStatus,
    quality: ConnectionQuality,
  ) => {
    switch (status) {
      case "failed":
        return {
          color: "text-red-400",
          bgColor: "bg-red-900/20",
          borderColor: "border-red-500/30",
          icon: "⚠️",
        };
      case "reconnecting":
        return quality.level === "critical"
          ? {
            color: "text-orange-400",
            bgColor: "bg-orange-900/20",
            borderColor: "border-orange-500/30",
            icon: "🔄",
          }
          : {
            color: "text-yellow-400",
            bgColor: "bg-yellow-900/20",
            borderColor: "border-yellow-500/30",
            icon: "🔄",
          };
      case "recovering":
        return {
          color: "text-blue-400",
          bgColor: "bg-blue-900/20",
          borderColor: "border-blue-500/30",
          icon: "🔄",
        };
      case "suspended":
        return {
          color: "text-purple-400",
          bgColor: "bg-purple-900/20",
          borderColor: "border-purple-500/30",
          icon: "⏸️",
        };
      case "connecting":
      case "initializing":
      case "preparing":
        return {
          color: "text-blue-400",
          bgColor: "bg-blue-900/20",
          borderColor: "border-blue-500/30",
          icon: "🔗",
        };
      case "processing":
      case "streaming":
        return {
          color: "text-green-400",
          bgColor: "bg-green-900/20",
          borderColor: "border-green-500/30",
          icon: "⚡",
        };
      case "completed":
        return {
          color: "text-green-500",
          bgColor: "bg-green-900/20",
          borderColor: "border-green-500/30",
          icon: "✅",
        };
      default:
        return {
          color: "text-gray-400",
          bgColor: "bg-gray-900/20",
          borderColor: "border-gray-500/30",
          icon: "🔗",
        };
    }
  };

  // Get connection quality indicator
  const getQualityIndicator = (quality: ConnectionQuality) => {
    switch (quality.level) {
      case "excellent":
        return { color: "text-green-400", bars: 4 };
      case "good":
        return { color: "text-green-400", bars: 3 };
      case "fair":
        return { color: "text-yellow-400", bars: 2 };
      case "poor":
        return { color: "text-orange-400", bars: 1 };
      case "critical":
        return { color: "text-red-400", bars: 0 };
      default:
        return { color: "text-gray-400", bars: 2 };
    }
  };

  // Format uptime
  const formatUptime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  // Render connection quality bars
  const renderQualityBars = () => {
    const { color, bars } = getQualityIndicator(quality);

    return (
      <div className="flex items-center gap-0.5">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className={`h-3 w-1 rounded-sm ${i < bars
              ? color.replace("text-", "bg-")
              : "bg-gray-600"
              }`}
          />
        ))}
      </div>
    );
  };

  // Progress bar component
  const ProgressBar = () => (
    <div className="h-1 w-full overflow-hidden rounded-full bg-gray-700/30">
      <motion.div
        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400"
        initial={{ width: 0 }}
        animate={{ width: `${progress}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </div>
  );

  // Retry indicator
  const RetryIndicator = () =>
    isRetrying &&
    retryCount > 0 && (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center gap-1 text-xs"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: "linear",
          }}
          className="h-3 w-3 text-orange-400"
        >
          🔄
        </motion.div>
        <span className="text-orange-400">Attempt {retryCount}</span>
      </motion.div>
    );

  // Compact mode render
  const renderCompact = () => {
    const styling = getStatusStyling(status, quality);

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.8 }}
        className={`flex items-center gap-2 rounded-lg px-3 py-2 ${styling.bgColor} ${styling.borderColor} border shadow-lg backdrop-blur-sm ${className} `}
      >
        <span className="text-sm">{styling.icon}</span>
        <span className={`text-sm font-medium ${styling.color}`}>
          {context}
        </span>
        {isRetrying && (
          <span className="text-xs text-orange-400">
            ({retryCount})
          </span>
        )}
      </motion.div>
    );
  };

  // Full mode render
  const renderFull = () => {
    const styling = getStatusStyling(status, quality);

    return (
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className={`min-w-[280px] max-w-[400px] rounded-lg border border-gray-700/50 bg-gray-900/95 px-4 py-3 shadow-xl backdrop-blur-md ${className} `}
      >
        {/* Status header */}
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm">{styling.icon}</span>
            <span
              className={`text-sm font-medium ${styling.color}`}
            >
              {context}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {renderQualityBars()}
            <RetryIndicator />
          </div>
        </div>

        {/* Current task */}
        {currentTask && currentTask !== context && (
          <div className="mb-2 truncate text-xs text-gray-400">
            {currentTask}
          </div>
        )}

        {/* Progress bar */}
        {(status === "processing" ||
          status === "streaming" ||
          status === "recovering") &&
          progress > 0 && (
            <div className="mb-2 space-y-1">
              <ProgressBar />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
            </div>
          )}

        {/* Connection metrics */}
        {showMetrics && (
          <div className="mt-2 grid grid-cols-2 gap-2 border-t border-gray-700/50 pt-2 text-xs text-gray-500">
            <div>
              <span className="text-gray-400">Latency:</span>{" "}
              {quality.latency}ms
            </div>
            <div>
              <span className="text-gray-400">Stability:</span>{" "}
              {Math.round(quality.stability * 100)}%
            </div>
            {uptime > 0 && (
              <div>
                <span className="text-gray-400">Uptime:</span>{" "}
                {formatUptime(uptime)}
              </div>
            )}
            {(requestsInFlight > 0 || queuedRequests > 0) && (
              <div>
                <span className="text-gray-400">Queue:</span>{" "}
                {requestsInFlight}+{queuedRequests}
              </div>
            )}
          </div>
        )}

        {/* Background activity indicator */}
        {backgroundActivity && (
          <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="h-2 w-2 rounded-full bg-blue-400"
            />
            <span>Background activity</span>
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <div
          className={`fixed ${getPositionClasses()} pointer-events-none z-50`}
        >
          {compactMode ? renderCompact() : renderFull()}
        </div>
      )}
    </AnimatePresence>
  );
};

export default ResilientConnectionStatus;
