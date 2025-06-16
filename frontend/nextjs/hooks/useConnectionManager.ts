import { useRef, useState, useEffect, useCallback } from "react";
import { Data, ChatBoxSettings } from "../types/data";
import { getHost } from "../helpers/getHost";

export type ConnectionStatus =
  | "idle"
  | "preparing"
  | "connecting"
  | "connected"
  | "processing"
  | "completed"
  | "reconnecting"
  | "recovering";

export type ResearchState = {
  status: ConnectionStatus;
  progress: number;
  currentTask: string;
  isRetrying: boolean;
  retryCount: number;
  lastError?: string;
};

interface ConnectionManagerConfig {
  maxRetries: number;
  baseRetryDelay: number;
  maxRetryDelay: number;
  heartbeatInterval: number;
  connectionTimeout: number;
}

const DEFAULT_CONFIG: ConnectionManagerConfig = {
  maxRetries: 10,
  baseRetryDelay: 1000,
  maxRetryDelay: 30000,
  heartbeatInterval: 30000,
  connectionTimeout: 10000,
};

export const useConnectionManager = (
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>,
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>,
  config: Partial<ConnectionManagerConfig> = {}
) => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [researchState, setResearchState] = useState<ResearchState>({
    status: "idle",
    progress: 0,
    currentTask: "",
    isRetrying: false,
    retryCount: 0,
  });

  // Refs for managing state across reconnections
  const heartbeatInterval = useRef<number>();
  const retryTimeout = useRef<number>();
  const connectionTimeout = useRef<number>();
  const currentRequest = useRef<any>(null);
  const messageBuffer = useRef<any[]>([]);
  const isIntentionalClose = useRef(false);
  const retryCount = useRef(0);
  const lastSuccessfulConnection = useRef<number>(Date.now());

  // Status descriptions for user-friendly display
  const getStatusDescription = (status: ConnectionStatus): string => {
    switch (status) {
      case "idle":
        return "Ready to research";
      case "preparing":
        return "Preparing research";
      case "connecting":
        return "Establishing connection";
      case "connected":
        return "Connected";
      case "processing":
        return "Analyzing information";
      case "completed":
        return "Research completed";
      case "reconnecting":
        return "Reconnecting";
      case "recovering":
        return "Recovering research";
      default:
        return "Ready";
    }
  };

  // Calculate exponential backoff delay
  const getRetryDelay = (attempt: number): number => {
    const delay = Math.min(
      finalConfig.baseRetryDelay * Math.pow(2, attempt),
      finalConfig.maxRetryDelay
    );
    // Add jitter to prevent thundering herd
    return delay + Math.random() * 1000;
  };

  // Update research state with progress tracking
  const updateResearchState = useCallback((updates: Partial<ResearchState>) => {
    setResearchState(prev => ({ ...prev, ...updates }));
  }, []);

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
      heartbeatInterval.current = undefined;
    }
    if (retryTimeout.current) {
      clearTimeout(retryTimeout.current);
      retryTimeout.current = undefined;
    }
    if (connectionTimeout.current) {
      clearTimeout(connectionTimeout.current);
      connectionTimeout.current = undefined;
    }
  }, []);

  // Start heartbeat monitoring
  const startHeartbeat = useCallback((ws: WebSocket) => {
    clearTimers();

    heartbeatInterval.current = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, finalConfig.heartbeatInterval);
  }, [finalConfig.heartbeatInterval, clearTimers]);

  // Handle successful connection
  const handleConnectionSuccess = useCallback((ws: WebSocket) => {
    lastSuccessfulConnection.current = Date.now();
    retryCount.current = 0;
    updateResearchState({
      status: "connected",
      isRetrying: false,
      retryCount: 0,
      lastError: undefined,
    });

    // Send buffered messages if any
    if (messageBuffer.current.length > 0) {
      updateResearchState({ status: "recovering", currentTask: "Resuming research" });
      messageBuffer.current.forEach(message => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(message);
        }
      });
      messageBuffer.current = [];
    }

    startHeartbeat(ws);
  }, [updateResearchState, startHeartbeat]);

  // Handle connection failure and retry logic
  const handleConnectionFailure = useCallback((error?: string) => {
    if (isIntentionalClose.current) {
      return;
    }

    retryCount.current++;
    const shouldRetry = retryCount.current <= finalConfig.maxRetries;

    updateResearchState({
      status: shouldRetry ? "reconnecting" : "idle",
      isRetrying: shouldRetry,
      retryCount: retryCount.current,
      lastError: error,
      currentTask: shouldRetry ? "Attempting to reconnect" : "Connection failed",
    });

    if (shouldRetry) {
      const delay = getRetryDelay(retryCount.current - 1);
      retryTimeout.current = window.setTimeout(() => {
        if (currentRequest.current && !isIntentionalClose.current) {
          initializeConnection(currentRequest.current.promptValue, currentRequest.current.chatBoxSettings);
        }
      }, delay);
    } else {
      setLoading(false);
      updateResearchState({
        status: "idle",
        currentTask: "Ready to research",
        isRetrying: false,
      });
    }
  }, [finalConfig.maxRetries, updateResearchState, setLoading]);

  // Process incoming WebSocket messages
  const processMessage = useCallback((data: any) => {
    // Update progress based on message type
    let progress = researchState.progress;
    let currentTask = researchState.currentTask;

    switch (data.type) {
      case "logs":
        progress = Math.min(progress + 10, 80);
        currentTask = "Gathering information";
        break;
      case "report":
        progress = Math.min(progress + 5, 95);
        currentTask = "Generating report";
        setAnswer((prev: string) => prev + data.output);
        break;
      case "path":
      case "chat":
        progress = 100;
        currentTask = "Research completed";
        updateResearchState({ status: "completed" });
        setLoading(false);
        break;
      case "human_feedback":
        if (data.content === "request") {
          setQuestionForHuman(data.output);
          setShowHumanFeedback(true);
          currentTask = "Awaiting feedback";
        }
        break;
    }

    updateResearchState({
      progress,
      currentTask,
      status: progress === 100 ? "completed" : "processing"
    });

    // Add to ordered data
    const contentAndType = `${data.content}-${data.type}`;
    setOrderedData((prevOrder) => [...prevOrder, { ...data, contentAndType }]);
  }, [researchState.progress, researchState.currentTask, updateResearchState, setAnswer, setLoading, setQuestionForHuman, setShowHumanFeedback, setOrderedData]);

  // Initialize WebSocket connection
  const initializeConnection = useCallback((promptValue: string, chatBoxSettings: ChatBoxSettings) => {
    if (isIntentionalClose.current) {
      return;
    }

    // Store current request for retry purposes
    currentRequest.current = { promptValue, chatBoxSettings };

    updateResearchState({
      status: retryCount.current > 0 ? "reconnecting" : "connecting",
      currentTask: retryCount.current > 0 ? "Reconnecting" : "Establishing connection",
      progress: 0,
    });

    try {
      const fullHost = getHost();
      const protocol = fullHost.includes("https") ? "wss:" : "ws:";
      const cleanHost = fullHost.replace("http://", "").replace("https://", "");
      const ws_uri = `${protocol}//${cleanHost}/ws`;

      const newSocket = new WebSocket(ws_uri);
      setSocket(newSocket);

      // Connection timeout
      connectionTimeout.current = window.setTimeout(() => {
        if (newSocket.readyState === WebSocket.CONNECTING) {
          newSocket.close();
          handleConnectionFailure("Connection timeout");
        }
      }, finalConfig.connectionTimeout);

      newSocket.onopen = () => {
        clearTimeout(connectionTimeout.current);
        handleConnectionSuccess(newSocket);

        // Prepare and send research request
        updateResearchState({
          status: "processing",
          currentTask: "Starting research",
          progress: 5,
        });

        const storedConfig = localStorage.getItem("apiVariables");
        const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
        const domainFilters = JSON.parse(localStorage.getItem("domainFilters") || "[]");
        const domains = domainFilters ? domainFilters.map((domain: any) => domain.value) : [];
        const { report_type, report_source, tone, mcp_enabled, mcp_configs } = chatBoxSettings;

        const requestData: any = {
          task: promptValue,
          report_type,
          report_source,
          tone,
          query_domains: domains
        };

        if (mcp_enabled && mcp_configs && mcp_configs.length > 0) {
          requestData.mcp_enabled = true;
          requestData.mcp_strategy = "fast";
          requestData.mcp_configs = mcp_configs;
        }

        const message = "start " + JSON.stringify(requestData);
        newSocket.send(message);
      };

      newSocket.onmessage = (event) => {
        try {
          if (event.data === "pong") {
            return;
          }

          const data = JSON.parse(event.data);
          processMessage(data);
        } catch (error) {
          console.error("Error processing message:", error);
        }
      };

      newSocket.onclose = (event) => {
        clearTimers();
        setSocket(null);

        if (!isIntentionalClose.current) {
          handleConnectionFailure(`Connection closed (${event.code})`);
        }
      };

      newSocket.onerror = () => {
        clearTimers();
        if (!isIntentionalClose.current) {
          handleConnectionFailure("Connection error");
        }
      };

    } catch (error) {
      handleConnectionFailure(`Failed to create connection: ${error}`);
    }
  }, [finalConfig.connectionTimeout, handleConnectionSuccess, handleConnectionFailure, updateResearchState, processMessage]);

  // Start research with connection management
  const startResearch = useCallback((promptValue: string, chatBoxSettings: ChatBoxSettings) => {
    isIntentionalClose.current = false;
    retryCount.current = 0;
    messageBuffer.current = [];

    updateResearchState({
      status: "preparing",
      currentTask: "Preparing research",
      progress: 0,
      isRetrying: false,
      retryCount: 0,
      lastError: undefined,
    });

    setLoading(true);
    initializeConnection(promptValue, chatBoxSettings);
  }, [initializeConnection, updateResearchState, setLoading]);

  // Stop research and close connection
  const stopResearch = useCallback(() => {
    isIntentionalClose.current = true;
    clearTimers();

    if (socket) {
      socket.close();
    }

    setSocket(null);
    setLoading(false);
    updateResearchState({
      status: "idle",
      currentTask: "Ready to research",
      progress: 0,
      isRetrying: false,
    });
  }, [socket, clearTimers, setLoading, updateResearchState]);

  // Send human feedback
  const sendFeedback = useCallback((feedback: string | null) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "human_feedback", content: feedback }));
    } else {
      // Buffer the message for when connection is restored
      messageBuffer.current.push(JSON.stringify({ type: "human_feedback", content: feedback }));
    }
    setShowHumanFeedback(false);
  }, [socket, setShowHumanFeedback]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isIntentionalClose.current = true;
      clearTimers();
      if (socket) {
        socket.close();
      }
    };
  }, [socket, clearTimers]);

  return {
    socket,
    researchState,
    startResearch,
    stopResearch,
    sendFeedback,
    getStatusDescription,
    isConnected: socket?.readyState === WebSocket.OPEN,
    isRetrying: researchState.isRetrying,
  };
};
