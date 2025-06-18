import { useRef, useState, useEffect, useCallback } from 'react';
import { Data, ChatBoxSettings, QuestionData } from '../types/data';
import { getHost } from '../helpers/getHost';
import {
  logWebSocketConnection,
  logWebSocketConnected,
  logWebSocketMessage,
  logWebSocketError,
  logWebSocketClosed,
  logAgentWork,
  logAgentComplete,
  logAgentError,
  logConnectionStatus,
  logConnectionRetry,
  logResearchProgress,
  logResearchComplete,
  logSystem,
  logUserAction,
  generateRequestId
} from "../utils/terminalLogger";
import { processWebSocketData } from "../utils/dataProcessing";

export const useWebSocket = (
  promptValue: string,
  chatBoxSettings: ChatBoxSettings,
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>,
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>,
) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const requestIdRef = useRef<string>(generateRequestId());
  const connectionAttemptRef = useRef<number>(0);
  const researchStartTime = useRef<number>(0);
  const agentActivityRef = useRef<Set<string>>(new Set());

  // Cleanup function for heartbeat
  useEffect(() => {
    return () => {
      if (socket) {
        logSystem("Cleaning up WebSocket connection", undefined, requestIdRef.current);
        socket.close(1000, "Component unmounting");
      }
    };
  }, [socket]);

  const heartbeatInterval = useRef<number>();

  const startHeartbeat = (ws: WebSocket) => {
    // Clear any existing heartbeat
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
    }

    // Start new heartbeat
    heartbeatInterval.current = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30000); // Send ping every 30 seconds
  };

  const initializeWebSocket = useCallback((promptValue: string, chatBoxSettings: ChatBoxSettings) => {
    console.log("🔌 WebSocket initialization called with:", { promptValue, chatBoxSettings });
    if (socket) {
      logSystem("WebSocket already exists, skipping initialization", undefined, requestIdRef.current);
      return;
    }

    const requestId = generateRequestId();
    requestIdRef.current = requestId;
    connectionAttemptRef.current += 1;
    researchStartTime.current = Date.now();

    logUserAction("Research initiated", {
      question: promptValue,
      settings: chatBoxSettings,
      attempt: connectionAttemptRef.current
    }, requestId);

    logSystem("WebSocket initialization called", {
      promptValue,
      chatBoxSettings,
      attempt: connectionAttemptRef.current
    }, requestId);

    const hostResult: HostResult = getHost();
    const protocol = hostResult.isSecure ? "wss://" : "ws://";
    const ws_uri = `${protocol}${hostResult.cleanHost}/ws`;

    logWebSocketConnection(ws_uri, requestId);
    logConnectionStatus("Initializing WebSocket connection", { host: hostResult.cleanHost, attempt: connectionAttemptRef.current }, requestId);

    const newSocket = new WebSocket(ws_uri);

    newSocket.onopen = () => {
      logWebSocketConnected(ws_uri, requestId);
      logConnectionStatus("WebSocket connected successfully", undefined, requestId);
      setIsConnected(true);
      setSocket(newSocket);

      // Reset connection attempts on successful connection
      connectionAttemptRef.current = 0;

      logResearchProgress("Initializing Research", 5, { question: promptValue }, requestId);
      logSystem("Sending research request with chatBoxSettings", chatBoxSettings, requestId);

      const data = {
        question: promptValue,
        report_type: chatBoxSettings.report_type,
        report_source: chatBoxSettings.report_source,
        tone: chatBoxSettings.tone,
        // headers: chatBoxSettings.headers, // Remove if not in ChatBoxSettings type
        ...(chatBoxSettings.mcp_enabled && {
          mcp_enabled: chatBoxSettings.mcp_enabled,
          mcp_configs: chatBoxSettings.mcp_configs
        })
      };

      // Log MCP configuration if enabled
      if (chatBoxSettings.mcp_enabled) {
        logSystem("Including MCP configuration", {
          mcp_enabled: chatBoxSettings.mcp_enabled,
          mcp_configs: chatBoxSettings.mcp_configs
        }, requestId);
      }

      logWebSocketMessage("SEND", data, requestId);
      newSocket.send(JSON.stringify(data));
    };

    newSocket.onmessage = (event) => {
      try {
        logWebSocketMessage("RECEIVE", event.data, requestId);

        // Check for ping/pong messages
        if (event.data === "pong") {
          logSystem("Received pong response", undefined, requestId);
          return;
        }

        const data = JSON.parse(event.data);
        logSystem("Parsed WebSocket data", data, requestId);

        // Extract and log agent work information
        if (data.type === "agent_work" || data.agent_type) {
          const agentType = data.agent_type || data.type;
          const task = data.task || data.message || "Processing";
          const progress = data.progress || undefined;

          logAgentWork(agentType, task, progress, requestId);
          agentActivityRef.current.add(agentType);

          if (progress !== undefined) {
            logResearchProgress(`${agentType} Progress`, progress, { task }, requestId);
          }
        }

        // Handle human feedback request
        if (data.type === "human_feedback") {
          logUserAction("Human feedback requested", data, requestId);
          setShowHumanFeedback(true);
          setQuestionForHuman(data.question || true);
        }

        // Process the data
        const processedData = processWebSocketData(data, setOrderedData, setAnswer);

        // Log research completion
        if (data.type === "report" || data.output) {
          logSystem("Received report data, updating answer", undefined, requestId);
          const elapsedTime = Date.now() - researchStartTime.current;
          logResearchComplete(elapsedTime, {
            reportLength: data.output?.length || 0,
            agentsUsed: Array.from(agentActivityRef.current),
            dataPoints: processedData?.length || 0
          }, requestId);
        }

        if (data.type === "end" || data.status === "complete") {
          logSystem("Research completed, stopping loading", undefined, requestId);
          setLoading(false);

          // Log completion summary
          const totalTime = Date.now() - researchStartTime.current;
          logAgentComplete("Research Session", {
            totalTimeMs: totalTime,
            agentsUsed: Array.from(agentActivityRef.current),
            question: promptValue
          }, requestId);
        }

      } catch (error) {
        logWebSocketError(error, requestId);
        logAgentError("WebSocket Message Processing", error, requestId);
      }
    };

    newSocket.onclose = (event) => {
      logWebSocketClosed(event.code, event.reason, requestId);
      logConnectionStatus("WebSocket connection closed", { code: event.code, reason: event.reason }, requestId);
      setIsConnected(false);
      setSocket(null);

      // Attempt reconnection if it wasn't a clean close
      if (event.code !== 1000 && connectionAttemptRef.current < 3) {
        const retryDelay = Math.pow(2, connectionAttemptRef.current) * 1000; // Exponential backoff
        logConnectionRetry(connectionAttemptRef.current + 1, 3, requestId);

        setTimeout(() => {
          logSystem("Attempting WebSocket reconnection", {
            attempt: connectionAttemptRef.current + 1,
            delay: retryDelay
          }, requestId);
          // Note: Need to store prompt and settings for reconnection
        }, retryDelay);
      } else if (connectionAttemptRef.current >= 3) {
        logSystem("Max WebSocket reconnection attempts reached", {
          maxAttempts: 3,
          finalCode: event.code,
          finalReason: event.reason
        }, requestId);
      }
    };

    newSocket.onerror = (error) => {
      logWebSocketError(error, requestId);
      logConnectionStatus("WebSocket error occurred", error, requestId);
    };
  }, [setAnswer, setLoading, setOrderedData, setQuestionForHuman, setShowHumanFeedback, socket]);

  useEffect(() => {
    if (promptValue) {
      // Reset agent activity tracking for new research
      agentActivityRef.current.clear();
      initializeWebSocket(promptValue, chatBoxSettings);
    }
  }, [promptValue, chatBoxSettings, initializeWebSocket]);

  return {
    socket,
    isConnected,
    requestId: requestIdRef.current,
    connectionAttempt: connectionAttemptRef.current,
    agentActivity: Array.from(agentActivityRef.current)
  };
};
