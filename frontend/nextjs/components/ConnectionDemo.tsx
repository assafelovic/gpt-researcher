import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  useResilientConnectionContext,
  useConnectionStatus,
  useResearch,
  useChat,
  useConnectionMetrics
} from "../hooks/useResilientConnectionContext";
import ResilientConnectionStatus from "./ResilientConnectionStatus";
import { ChatBoxSettings } from "../types/data";

// Example integration component showing best practices
const ConnectionDemo: React.FC = () => {
  const [researchQuery, setResearchQuery] = useState('');
  const [chatMessage, setChatMessage] = useState('');

  // Use specialized hooks for different functionalities
  const connectionStatus = useConnectionStatus();
  const { startResearch, isProcessing, progress, currentTask, canStartResearch } = useResearch();
  const { sendChatMessage, canChat } = useChat();
  const { queueStatus, quality, uptime } = useConnectionMetrics();

  // Full context for advanced usage
  const {
    connectionState,
    isConnected,
    isConnecting,
    hasError,
    reconnect,
    shouldShowStatus
  } = useResilientConnectionContext();

  const handleStartResearch = () => {
    if (!researchQuery.trim() || !canStartResearch) return;

    const chatBoxSettings: ChatBoxSettings = {
      report_type: "research_report",
      report_source: "web",
      tone: "objective",
      domains: [],
      defaultReportType: "research_report",
      mcp_enabled: false,
      mcp_configs: [],
    };

    startResearch(researchQuery, chatBoxSettings);
  };

  const handleSendChat = () => {
    if (!chatMessage.trim() || !canChat) return;

    sendChatMessage(chatMessage);
    setChatMessage("");
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
      case "ready":
        return "text-green-400";
      case "connecting":
      case "reconnecting":
      case "preparing":
        return "text-yellow-400";
      case "failed":
        return "text-red-400";
      case "processing":
      case "streaming":
        return "text-blue-400";
      default:
        return "text-gray-400";
    }
  };

  const getQualityColor = (level: string) => {
    switch (level) {
      case "excellent":
        return "text-green-400";
      case "good":
        return "text-green-300";
      case "fair":
        return "text-yellow-400";
      case "poor":
        return "text-orange-400";
      case "critical":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  const formatUptime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Resilient Connection Status - Shows automatically when needed */}
      <ResilientConnectionStatus
        connectionState={connectionState}
        showMetrics={true}
        position="top-center"
      />

      {/* Connection Overview Dashboard */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6"
      >
        <h2 className="text-xl font-semibold text-white mb-4">
          Resilient Connection System Demo
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Connection Status */}
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Connection Status</h3>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-400" :
                isConnecting ? "bg-yellow-400" :
                  hasError ? "bg-red-400" : "bg-gray-400"
                }`} />
              <span className={`text-sm font-medium ${getStatusColor(connectionStatus.status)}`}>
                {connectionStatus.message}
              </span>
            </div>
            {connectionStatus.retryCount > 0 && (
              <div className="text-xs text-orange-400 mt-1">
                Retry attempts: {connectionStatus.retryCount}
              </div>
            )}
          </div>

          {/* Connection Quality */}
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Connection Quality</h3>
            <div className="flex items-center gap-2">
              <div className="flex gap-0.5">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-1 h-4 rounded-sm ${i < (quality.level === 'excellent' ? 4 :
                      quality.level === "good" ? 3 :
                        quality.level === "fair" ? 2 :
                          quality.level === "poor" ? 1 : 0)
                      ? getQualityColor(quality.level).replace("text-", "bg-")
                      : "bg-gray-600"
                      }`}
                  />
                ))}
              </div>
              <span className={`text-sm font-medium capitalize ${getQualityColor(quality.level)}`}>
                {quality.level}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Latency: {quality.latency}ms | Stability: {Math.round(quality.stability * 100)}%
            </div>
          </div>

          {/* System Metrics */}
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-2">System Metrics</h3>
            <div className="space-y-1 text-sm">
              <div className="text-gray-300">
                Uptime: {formatUptime(uptime)}
              </div>
              {queueStatus.total > 0 && (
                <div className="text-blue-400">
                  Queue: {queueStatus.active} active, {queueStatus.queued} waiting
                </div>
              )}
              {connectionState.backgroundActivity && (
                <div className="text-green-400 text-xs">
                  • Background activity
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Manual Controls */}
        <div className="flex gap-3">
          {hasError && (
            <button
              onClick={reconnect}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Retry Connection
            </button>
          )}

          <div className="text-xs text-gray-500 flex items-center">
            Auto-reconnect: ✓ | Silent retries: ✓ | Context preservation: ✓
          </div>
        </div>
      </motion.div>

      {/* Research Interface */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4">
          Research Interface
        </h3>

        <div className="space-y-4">
          <div>
            <textarea
              value={researchQuery}
              onChange={(e) => setResearchQuery(e.target.value)}
              placeholder="Enter your research query..."
              className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 resize-none"
              rows={3}
              disabled={!canStartResearch}
            />
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={handleStartResearch}
              disabled={!canStartResearch || !researchQuery.trim() || isProcessing}
              className="px-6 py-2 bg-teal-600 hover:bg-teal-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
            >
              {isProcessing ? "Researching..." : "Start Research"}
            </button>

            {isProcessing && (
              <div className="flex items-center gap-3">
                <div className="text-sm text-gray-400">
                  {currentTask || "Processing..."}
                </div>
                <div className="w-32 bg-gray-700 rounded-full h-2">
                  <motion.div
                    className="bg-teal-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <span className="text-sm text-gray-400">{progress}%</span>
              </div>
            )}
          </div>

          {!canStartResearch && (
            <div className="text-sm text-yellow-400">
              ⚠️ Connection not ready for research. {connectionStatus.message}
            </div>
          )}
        </div>
      </motion.div>

      {/* Chat Interface */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4">
          Chat Interface
        </h3>

        <div className="space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Ask a follow-up question..."
              className="flex-1 p-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400"
              disabled={!canChat}
              onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
            />
            <button
              onClick={handleSendChat}
              disabled={!canChat || !chatMessage.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
            >
              Send
            </button>
          </div>

          {!canChat && (
            <div className="text-sm text-yellow-400">
              ⚠️ Chat not available. Complete a research task first.
            </div>
          )}
        </div>
      </motion.div>

      {/* Integration Features */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4">
          Key Features Demonstrated
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <h4 className="font-medium text-teal-400">Connection Resilience</h4>
            <ul className="text-gray-300 space-y-1">
              <li>✅ Automatic reconnection with exponential backoff</li>
              <li>✅ Silent management of connection states</li>
              <li>✅ Request queuing and recovery</li>
              <li>✅ Network status awareness</li>
              <li>✅ Tab visibility detection</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium text-teal-400">User Experience</h4>
            <ul className="text-gray-300 space-y-1">
              <li>✅ Minimal, contextual feedback</li>
              <li>✅ Transparent error handling</li>
              <li>✅ Progress tracking</li>
              <li>✅ Quality monitoring</li>
              <li>✅ Background activity indication</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium text-teal-400">Security & Privacy</h4>
            <ul className="text-gray-300 space-y-1">
              <li>✅ Error sanitization</li>
              <li>✅ Rate limiting</li>
              <li>✅ Connection limits</li>
              <li>✅ No sensitive backend exposure</li>
              <li>✅ Secure message handling</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium text-teal-400">Developer Experience</h4>
            <ul className="text-gray-300 space-y-1">
              <li>✅ Specialized hooks for different needs</li>
              <li>✅ Context provider architecture</li>
              <li>✅ TypeScript support</li>
              <li>✅ Configurable behavior</li>
              <li>✅ Metrics and monitoring</li>
            </ul>
          </div>
        </div>
      </motion.div>

      {/* Configuration Example */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4">
          Configuration Example
        </h3>

        <pre className="bg-gray-800 rounded-lg p-4 text-sm text-gray-300 overflow-x-auto">
          {`// In your app's root component
<ResilientConnectionProvider
  setOrderedData={setOrderedData}
  setAnswer={setAnswer}
  setLoading={setLoading}
  setShowHumanFeedback={setShowHumanFeedback}
  setQuestionForHuman={setQuestionForHuman}
  config={{
    maxRetries: 15,
    baseRetryDelay: 1000,
    maxRetryDelay: 30000,
    silentRetryThreshold: 3,
    sanitizeErrors: true,
    logLevel: "warnings",
    enableMetrics: true
  }}
>
  <YourApp />
</ResilientConnectionProvider>

// In your components
const { startResearch, isProcessing } = useResearch();
const { sendChatMessage, canChat } = useChat();
const connectionStatus = useConnectionStatus();`}
        </pre>
      </motion.div>
    </div>
  );
};

export default ConnectionDemo;
