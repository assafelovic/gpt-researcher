import { useRef, useState, useEffect, useCallback, useMemo } from "react";
import { Data, ChatBoxSettings } from "../types/data";
import { getHost } from "../helpers/getHost";
import {
  logConnectionStatus,
  logConnectionRetry,
  logWebSocketConnection,
  logWebSocketConnected,
  logWebSocketError,
  logWebSocketClosed,
  logWebSocketMessage,
  logAgentWork,
  logResearchProgress,
  logSystem,
  logError,
  logWarning,
  generateRequestId
} from "../utils/terminalLogger";

// Connection states with detailed status tracking
export type ConnectionStatus =
  | "idle"
  | "initializing"
  | "connecting"
  | "connected"
  | "authenticating"
  | "ready"
  | "preparing"
  | "processing"
  | "streaming"
  | "completed"
  | "reconnecting"
  | "recovering"
  | "suspended"
  | "failed";

// Enhanced connection quality metrics
export interface ConnectionQuality {
  level: "excellent" | "good" | "fair" | "poor" | "critical";
  latency: number;
  stability: number;
  throughput: number;
  errorRate: number;
  consecutiveSuccesses: number;
  consecutiveFailures: number;
  lastSuccessTime: number;
  predictedQuality: "excellent" | "good" | "fair" | "poor" | "critical";
}

// Request queue for preserving user actions
interface QueuedRequest {
  id: string;
  type: "research" | "chat" | "ping" | "status";
  payload: any;
  timestamp: number;
  priority: "low" | "normal" | "high" | "critical";
  retryCount: number;
  maxRetries: number;
  onSuccess?: (result: any) => void;
  onFailure?: (error: any) => void;
  metadata?: Record<string, any>;
}

// Enhanced connection state
export interface ResilientConnectionState {
  status: ConnectionStatus;
  quality: ConnectionQuality;
  progress: number;
  currentTask: string;
  isRetrying: boolean;
  retryCount: number;
  totalRetries: number;
  lastError?: string;
  uptime: number;
  requestsInFlight: number;
  queuedRequests: number;
  backgroundActivity: boolean;
  context: string;
  userFeedbackLevel: "none" | "minimal" | "contextual" | "detailed";
}

// Advanced configuration options
interface ResilientConnectionConfig {
  // Retry configuration
  maxRetries: number;
  baseRetryDelay: number;
  maxRetryDelay: number;
  retryBackoffFactor: number;
  jitterRange: number;

  // Connection timeouts
  connectionTimeout: number;
  reconnectionTimeout: number;
  heartbeatInterval: number;
  healthCheckInterval: number;

  // Quality thresholds
  latencyThresholds: {
    excellent: number;
    good: number;
    fair: number;
    poor: number;
  };

  // Request management
  maxQueueSize: number;
  requestTimeout: number;
  batchSize: number;
  priorityWeights: Record<string, number>;

  // User experience
  silentRetryThreshold: number;
  contextualFeedbackDelay: number;
  progressUpdateInterval: number;

  // Security and privacy
  sanitizeErrors: boolean;
  logLevel: "none" | "errors" | "warnings" | "info" | "debug";
  enableMetrics: boolean;
}

const DEFAULT_CONFIG: ResilientConnectionConfig = {
  maxRetries: 15,
  baseRetryDelay: 1000,
  maxRetryDelay: 30000,
  retryBackoffFactor: 1.5,
  jitterRange: 0.2,

  connectionTimeout: 10000,
  reconnectionTimeout: 5000,
  heartbeatInterval: 30000,
  healthCheckInterval: 5000,

  latencyThresholds: {
    excellent: 100,
    good: 300,
    fair: 1000,
    poor: 3000,
  },

  maxQueueSize: 100,
  requestTimeout: 60000,
  batchSize: 5,
  priorityWeights: {
    critical: 1000,
    high: 100,
    normal: 10,
    low: 1,
  },

  silentRetryThreshold: 3,
  contextualFeedbackDelay: 2000,
  progressUpdateInterval: 500,

  sanitizeErrors: true,
  logLevel: "warnings",
  enableMetrics: true,
};

export const useResilientConnection = (
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>,
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>,
  config: Partial<ResilientConnectionConfig> = {},
) => {
  const finalConfig = useMemo(
    () => ({ ...DEFAULT_CONFIG, ...config }),
    [config],
  );

  // Core connection state
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionState, setConnectionState] =
    useState<ResilientConnectionState>({
      status: "idle",
      quality: {
        level: "good",
        latency: 0,
        stability: 1,
        throughput: 0,
        errorRate: 0,
        consecutiveSuccesses: 0,
        consecutiveFailures: 0,
        lastSuccessTime: 0,
        predictedQuality: "good",
      },
      progress: 0,
      currentTask: "",
      isRetrying: false,
      retryCount: 0,
      totalRetries: 0,
      uptime: 0,
      requestsInFlight: 0,
      queuedRequests: 0,
      backgroundActivity: false,
      context: "Ready to research",
      userFeedbackLevel: "none",
    });

  // Internal state management
  const requestQueue = useRef<QueuedRequest[]>([]);
  const activeRequests = useRef<Map<string, QueuedRequest>>(new Map());
  const connectionStartTime = useRef<number>(0);
  const lastActivityTime = useRef<number>(Date.now());
  const retryTimeouts = useRef<Map<string, number>>(new Map());

  // Timers and intervals
  const heartbeatInterval = useRef<number>();
  const healthCheckInterval = useRef<number>();
  const progressUpdateInterval = useRef<number>();
  const connectionTimeout = useRef<number>();

  // Metrics and monitoring
  const metrics = useRef({
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    totalLatency: 0,
    latencyHistory: [] as number[],
    errorHistory: [] as {
      timestamp: number;
      error: string;
      context: string;
    }[],
    uptimeHistory: [] as { start: number; end?: number }[],
  });

  // Enhanced error sanitization
  const sanitizeError = useCallback(
    (error: any): string => {
      if (!finalConfig.sanitizeErrors) return String(error);

      const errorStr = String(error);

      // Remove sensitive information patterns
      return errorStr
        .replace(
          /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
          "[email]",
        )
        .replace(
          /\b(?:token|key|secret|password|auth)[=:]\s*[^\s]+/gi,
          "[auth]",
        )
        .replace(
          /\b(?:localhost|127\.0\.0\.1|\d+\.\d+\.\d+\.\d+):\d+/g,
          "[server]",
        )
        .replace(
          /\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b/gi,
          "[uuid]",
        )
        .substring(0, 200); // Limit error message length
    },
    [finalConfig.sanitizeErrors],
  );

  // Intelligent retry delay calculation with jitter
  const calculateRetryDelay = useCallback(
    (
      attempt: number,
      baseDelay: number = finalConfig.baseRetryDelay,
    ): number => {
      const exponentialDelay = Math.min(
        baseDelay * Math.pow(finalConfig.retryBackoffFactor, attempt),
        finalConfig.maxRetryDelay,
      );

      // Add jitter to prevent thundering herd
      const jitter =
        exponentialDelay *
        finalConfig.jitterRange *
        (Math.random() - 0.5);
      return Math.max(1000, exponentialDelay + jitter);
    },
    [finalConfig],
  );

  // Advanced connection quality assessment
  const assessConnectionQuality = useCallback(
    (
      latency: number,
      errorRate: number,
      stability: number,
    ): ConnectionQuality["level"] => {
      const { latencyThresholds } = finalConfig;

      // Predictive quality based on trends
      const recentLatencies = metrics.current.latencyHistory.slice(-10);
      const latencyTrend =
        recentLatencies.length > 1
          ? recentLatencies[recentLatencies.length - 1] -
          recentLatencies[0]
          : 0;

      // Base quality assessment
      let baseQuality: ConnectionQuality["level"] = "good";

      if (errorRate > 0.3 || stability < 0.3) {
        baseQuality = "critical";
      } else if (latency > latencyThresholds.poor || errorRate > 0.2) {
        baseQuality = "poor";
      } else if (latency > latencyThresholds.fair || errorRate > 0.1) {
        baseQuality = "fair";
      } else if (latency > latencyThresholds.good || errorRate > 0.05) {
        baseQuality = "good";
      } else if (
        latency <= latencyThresholds.excellent &&
        errorRate <= 0.01 &&
        stability > 0.9
      ) {
        baseQuality = "excellent";
      }

      // Apply trend adjustment
      if (latencyTrend > 100 && baseQuality !== "critical") {
        const qualityLevels: ConnectionQuality["level"][] = [
          "excellent",
          "good",
          "fair",
          "poor",
          "critical",
        ];
        const currentIndex = qualityLevels.indexOf(baseQuality);
        baseQuality =
          qualityLevels[
          Math.min(currentIndex + 1, qualityLevels.length - 1)
          ];
      }

      return baseQuality;
    },
    [finalConfig],
  );

  // Update connection state with enhanced context
  const updateConnectionState = useCallback(
    (updates: Partial<ResilientConnectionState>) => {
      setConnectionState((prev) => {
        const newState = { ...prev, ...updates };

        // Auto-adjust user feedback level based on context
        if (
          newState.status === "failed" ||
          newState.retryCount > finalConfig.silentRetryThreshold
        ) {
          newState.userFeedbackLevel = "contextual";
        } else if (
          newState.status === "reconnecting" ||
          newState.isRetrying
        ) {
          newState.userFeedbackLevel = "minimal";
        } else if (
          newState.status === "connected" ||
          newState.status === "ready"
        ) {
          newState.userFeedbackLevel = "none";
        }

        return newState;
      });
    },
    [finalConfig.silentRetryThreshold],
  );

  // Generate contextual user feedback messages
  const getContextualMessage = useCallback(
    (status: ConnectionStatus, context: any = {}): string => {
      const { retryCount, quality, currentTask } = context;

      switch (status) {
        case "initializing":
          return "Starting research session";
        case "connecting":
          return retryCount > 0
            ? "Reconnecting to research engine"
            : "Connecting to research engine";
        case "authenticating":
          return "Securing connection";
        case "ready":
          return "Ready to research";
        case "preparing":
          return "Preparing research request";
        case "processing":
          return currentTask || "Processing research request";
        case "streaming":
          return "Receiving research data";
        case "reconnecting":
          return quality?.level === "critical"
            ? "Experiencing connectivity issues, working to restore service"
            : "Brief connection interruption, reconnecting";
        case "recovering":
          return "Resuming research where we left off";
        case "suspended":
          return "Research paused due to connection issues";
        case "failed":
          return "Unable to establish stable connection";
        default:
          return "Ready to research";
      }
    },
    [],
  );

  // Queue management with priority handling
  const enqueueRequest = useCallback(
    (request: Omit<QueuedRequest, "id" | "timestamp">) => {
      if (requestQueue.current.length >= finalConfig.maxQueueSize) {
        // Remove lowest priority request
        const lowestPriorityIndex = requestQueue.current.reduce(
          (minIndex, req, index) => {
            const minPriority =
              finalConfig.priorityWeights[
              requestQueue.current[minIndex].priority
              ];
            const currentPriority =
              finalConfig.priorityWeights[req.priority];
            return currentPriority < minPriority ? index : minIndex;
          },
          0,
        );

        requestQueue.current.splice(lowestPriorityIndex, 1);
      }

      const queuedRequest: QueuedRequest = {
        ...request,
        id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
      };

      // Insert request based on priority
      const priority = finalConfig.priorityWeights[request.priority];
      let insertIndex = requestQueue.current.length;

      for (let i = 0; i < requestQueue.current.length; i++) {
        const queuePriority =
          finalConfig.priorityWeights[
          requestQueue.current[i].priority
          ];
        if (priority > queuePriority) {
          insertIndex = i;
          break;
        }
      }

      requestQueue.current.splice(insertIndex, 0, queuedRequest);

      updateConnectionState({
        queuedRequests: requestQueue.current.length,
      });

      return queuedRequest.id;
    },
    [finalConfig, updateConnectionState],
  );

  // Process queued requests
  const processRequestQueue = useCallback(async () => {
    if (
      !socket ||
      socket.readyState !== WebSocket.OPEN ||
      requestQueue.current.length === 0
    ) {
      return;
    }

    const batchSize = Math.min(
      finalConfig.batchSize,
      requestQueue.current.length,
    );
    const requestsToProcess = requestQueue.current.splice(0, batchSize);

    for (const request of requestsToProcess) {
      activeRequests.current.set(request.id, request);

      try {
        const message =
          request.type === "research"
            ? `start ${JSON.stringify(request.payload)}`
            : JSON.stringify({
              type: request.type,
              ...request.payload,
            });

        socket.send(message);

        updateConnectionState({
          requestsInFlight: activeRequests.current.size,
          queuedRequests: requestQueue.current.length,
        });

        // Set request timeout
        setTimeout(() => {
          if (activeRequests.current.has(request.id)) {
            activeRequests.current.delete(request.id);
            request.onFailure?.({
              error: "Request timeout",
              requestId: request.id,
            });
          }
        }, finalConfig.requestTimeout);
      } catch (error) {
        activeRequests.current.delete(request.id);
        request.onFailure?.({
          error: sanitizeError(error),
          requestId: request.id,
        });
      }
    }
  }, [socket, finalConfig, sanitizeError, updateConnectionState]);

  // Enhanced WebSocket message handler
  const handleWebSocketMessage = useCallback(
    (event: MessageEvent) => {
      lastActivityTime.current = Date.now();

      try {
        // Handle ping/pong
        if (event.data === "pong") {
          const latency = Date.now() - metrics.current.totalLatency;
          metrics.current.latencyHistory.push(latency);
          if (metrics.current.latencyHistory.length > 50) {
            metrics.current.latencyHistory =
              metrics.current.latencyHistory.slice(-50);
          }
          return;
        }

        // Parse message data
        const data = JSON.parse(event.data);

        // Update metrics
        metrics.current.successfulRequests++;

        // Handle different message types
        switch (data.type) {
          case "human_feedback":
            if (data.content === "request") {
              setQuestionForHuman(data.output);
              setShowHumanFeedback(true);
              updateConnectionState({
                status: "suspended",
                currentTask: "Waiting for human input",
                context:
                  "User input required to continue research",
              });
            }
            break;

          case "logs":
            updateConnectionState({
              status: "processing",
              progress: Math.min(
                connectionState.progress + 5,
                80,
              ),
              currentTask: "Gathering information",
              backgroundActivity: true,
            });
            break;

          case "report":
            setAnswer((prev: string) => prev + data.output);
            updateConnectionState({
              status: "streaming",
              progress: Math.min(
                connectionState.progress + 10,
                95,
              ),
              currentTask: "Generating report",
            });
            break;

          case "path":
          case "chat":
            setLoading(false);
            updateConnectionState({
              status: "completed",
              progress: 100,
              currentTask: "Research completed",
              backgroundActivity: false,
            });
            break;
        }

        // Add to ordered data
        const contentAndType = `${data.content}-${data.type}`;
        setOrderedData((prevOrder) => [
          ...prevOrder,
          { ...data, contentAndType },
        ]);

        // Update connection quality
        const avgLatency =
          metrics.current.latencyHistory.length > 0
            ? metrics.current.latencyHistory.reduce(
              (sum, lat) => sum + lat,
              0,
            ) / metrics.current.latencyHistory.length
            : 0;

        const errorRate =
          metrics.current.totalRequests > 0
            ? metrics.current.failedRequests /
            metrics.current.totalRequests
            : 0;

        const stability =
          metrics.current.successfulRequests /
          Math.max(1, metrics.current.totalRequests);

        updateConnectionState({
          quality: {
            ...connectionState.quality,
            level: assessConnectionQuality(
              avgLatency,
              errorRate,
              stability,
            ),
            latency: Math.round(avgLatency),
            stability: Math.round(stability * 100) / 100,
            errorRate: Math.round(errorRate * 100) / 100,
            consecutiveSuccesses:
              connectionState.quality.consecutiveSuccesses + 1,
            consecutiveFailures: 0,
            lastSuccessTime: Date.now(),
          },
        });
      } catch (error) {
        if (finalConfig.logLevel !== "none") {
          console.warn(
            "Error parsing WebSocket message:",
            sanitizeError(error),
          );
        }

        metrics.current.failedRequests++;
        updateConnectionState({
          quality: {
            ...connectionState.quality,
            consecutiveFailures:
              connectionState.quality.consecutiveFailures + 1,
            consecutiveSuccesses: 0,
          },
        });
      }
    },
    [
      connectionState,
      setOrderedData,
      setAnswer,
      setLoading,
      setShowHumanFeedback,
      setQuestionForHuman,
      sanitizeError,
      assessConnectionQuality,
      updateConnectionState,
      finalConfig.logLevel,
    ],
  );

  // Initialize WebSocket connection with enhanced error handling
  const initializeConnection = useCallback(
    async (promptValue?: string, chatBoxSettings?: ChatBoxSettings) => {
      const requestId: string = generateRequestId();

      if (socket && socket.readyState === WebSocket.OPEN) {
        logSystem('WebSocket already connected, skipping initialization', {
          currentState: socket.readyState
        }, requestId);

        if (finalConfig.logLevel === "debug") {
          console.log(
            "WebSocket already connected, skipping initialization",
          );
        }
        return;
      }

      logConnectionStatus('Initializing resilient connection', {
        hasPrompt: !!promptValue,
        hasSettings: !!chatBoxSettings,
        connectionAttempts: connectionState.retryCount
      }, requestId);

      // Clear existing timers
      if (heartbeatInterval.current)
        clearInterval(heartbeatInterval.current);
      if (healthCheckInterval.current)
        clearInterval(healthCheckInterval.current);
      if (connectionTimeout.current)
        clearTimeout(connectionTimeout.current);

      updateConnectionState({
        status: "initializing",
        context: "Preparing connection to research engine",
      });

      try {
        const fullHost = getHost();
        const protocol = fullHost.includes("https") ? "wss:" : "ws:";
        const cleanHost = fullHost.replace(/^https?:\/\//, "");
        const wsUri = `${protocol}//${cleanHost}/ws`;

        logWebSocketConnection(wsUri, requestId);
        logConnectionStatus('Establishing WebSocket connection', {
          protocol,
          host: cleanHost,
          timeout: finalConfig.connectionTimeout
        }, requestId);

        updateConnectionState({
          status: "connecting",
          context: "Establishing secure connection",
        });

        const newSocket = new WebSocket(wsUri);

        // Connection timeout
        connectionTimeout.current = window.setTimeout(() => {
          if (newSocket.readyState === WebSocket.CONNECTING) {
            logError('Connection timeout exceeded', {
              timeout: finalConfig.connectionTimeout,
              uri: wsUri
            }, requestId);
            newSocket.close();
            handleConnectionFailure("Connection timeout");
          }
        }, finalConfig.connectionTimeout);

        newSocket.onopen = () => {
          clearTimeout(connectionTimeout.current);
          connectionStartTime.current = Date.now();

          logWebSocketConnected(wsUri, requestId);
          setSocket(newSocket);

          updateConnectionState({
            status: "connected",
            context: "Connected to research engine",
            retryCount: 0,
            isRetrying: false,
            uptime: 0,
          });

          logConnectionStatus('Connection established successfully', {
            connectionTime: Date.now() - connectionStartTime.current,
            heartbeatInterval: finalConfig.heartbeatInterval
          }, requestId);

          // Start heartbeat
          heartbeatInterval.current = window.setInterval(() => {
            if (newSocket.readyState === WebSocket.OPEN) {
              newSocket.send("ping");
            }
          }, finalConfig.heartbeatInterval);

          // Process initial request if provided
          if (promptValue && chatBoxSettings) {
            logSystem('Processing initial research request', {
              question: promptValue,
              settings: chatBoxSettings
            }, requestId);

            const enqueueRequestId = enqueueRequest({
              type: "research",
              payload: buildResearchRequest(
                promptValue,
                chatBoxSettings,
              ),
              priority: "high",
              retryCount: 0,
              maxRetries: 3,
            });

            processRequestQueue();
          }

          updateConnectionState({
            status: "ready",
            context: getContextualMessage("ready"),
          });
        };

        newSocket.onmessage = handleWebSocketMessage;

        newSocket.onclose = (event: any) => {
          clearTimeout(connectionTimeout.current);
          if (heartbeatInterval.current)
            clearInterval(heartbeatInterval.current);

          logWebSocketClosed(event.code, event.reason, requestId);
          setSocket(null);

          if (connectionState.status !== "failed") {
            handleConnectionFailure(
              "Connection closed unexpectedly",
            );
          }
        };

        newSocket.onerror = (error: any) => {
          clearTimeout(connectionTimeout.current);
          logWebSocketError(error, requestId);
          handleConnectionFailure(
            `Connection error: ${sanitizeError(error)}`,
          );
        };
      } catch (error) {
        logError('Failed to initialize connection', error, requestId);
        handleConnectionFailure(
          `Failed to initialize connection: ${sanitizeError(error)}`,
        );
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      socket,
      finalConfig,
      updateConnectionState,
      getContextualMessage,
      enqueueRequest,
      processRequestQueue,
      handleWebSocketMessage,
      sanitizeError,
      connectionState.status,
    ],
  );

  // Build research request payload
  const buildResearchRequest = useCallback(
    (promptValue: string, chatBoxSettings: ChatBoxSettings) => {
      const storedConfig = localStorage.getItem("apiVariables");
      const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};

      const domainFilters = JSON.parse(
        localStorage.getItem("domainFilters") || "[]",
      );
      const domains = domainFilters
        ? domainFilters.map((domain: any) => domain.value)
        : [];

      const {
        report_type,
        report_source,
        tone,
        mcp_enabled,
        mcp_configs,
      } = chatBoxSettings;

      const requestData: any = {
        task: promptValue,
        report_type,
        report_source,
        tone,
        query_domains: domains,
      };

      if (mcp_enabled && mcp_configs && mcp_configs.length > 0) {
        requestData.mcp_enabled = true;
        requestData.mcp_strategy = "fast";
        requestData.mcp_configs = mcp_configs;
      }

      return requestData;
    },
    [],
  );

  // Enhanced connection failure handling
  const handleConnectionFailure = useCallback(
    (error: string) => {
      const requestId = generateRequestId();
      const sanitizedError = sanitizeError(error);

      logError('Connection failure detected', {
        error: sanitizedError,
        currentStatus: connectionState.status,
        retryCount: connectionState.retryCount,
        maxRetries: finalConfig.maxRetries
      }, requestId);

      // Record error in metrics
      metrics.current.failedRequests++;
      metrics.current.errorHistory.push({
        timestamp: Date.now(),
        error: sanitizedError,
        context: connectionState.context,
      });

      // Keep only recent error history
      if (metrics.current.errorHistory.length > 100) {
        metrics.current.errorHistory = metrics.current.errorHistory.slice(-50);
      }

      // Assess if we should retry
      if (connectionState.retryCount < finalConfig.maxRetries) {
        const retryDelay = Math.min(
          finalConfig.baseRetryDelay *
          Math.pow(finalConfig.retryBackoffFactor, connectionState.retryCount),
          finalConfig.maxRetryDelay,
        );

        const jitter =
          retryDelay * finalConfig.jitterRange * (Math.random() - 0.5);
        const finalDelay = Math.max(retryDelay + jitter, 1000);

        logConnectionRetry(
          connectionState.retryCount + 1,
          finalConfig.maxRetries,
          requestId
        );

        logSystem('Scheduling connection retry', {
          retryDelay: finalDelay,
          attempt: connectionState.retryCount + 1,
          error: sanitizedError
        }, requestId);

        updateConnectionState({
          status: "reconnecting",
          context: getContextualMessage("reconnecting"),
          isRetrying: true,
          retryCount: connectionState.retryCount + 1,
          totalRetries: connectionState.totalRetries + 1,
          lastError: sanitizedError,
        });

        // Schedule retry
        setTimeout(() => {
          logConnectionRetry(connectionState.retryCount, finalConfig.maxRetries, requestId);
          initializeConnection();
        }, finalDelay);
      } else {
        // Max retries exceeded
        logError('Max connection retries exceeded', {
          maxRetries: finalConfig.maxRetries,
          totalFailures: connectionState.totalRetries + 1,
          finalError: sanitizedError
        }, requestId);

        updateConnectionState({
          status: "failed",
          context: getContextualMessage("failed"),
          isRetrying: false,
          lastError: sanitizedError,
        });

        setLoading(false);
      }
    },
    [
      sanitizeError,
      connectionState,
      finalConfig,
      updateConnectionState,
      getContextualMessage,
      initializeConnection,
      setLoading,
    ],
  );

  // Public API methods
  const startResearch = useCallback(
    (promptValue: string, chatBoxSettings: ChatBoxSettings) => {
      setLoading(true);
      setAnswer("");
      setOrderedData([]);

      updateConnectionState({
        status: "preparing",
        progress: 0,
        currentTask: "Preparing research request",
        context: "Starting new research session",
      });

      if (socket && socket.readyState === WebSocket.OPEN) {
        const requestId = enqueueRequest({
          type: "research",
          payload: buildResearchRequest(promptValue, chatBoxSettings),
          priority: "high",
          retryCount: 0,
          maxRetries: 3,
        });

        processRequestQueue();
      } else {
        initializeConnection(promptValue, chatBoxSettings);
      }
    },
    [
      socket,
      setLoading,
      setAnswer,
      setOrderedData,
      updateConnectionState,
      enqueueRequest,
      processRequestQueue,
      initializeConnection,
      buildResearchRequest,
    ],
  );

  // Chat with context preservation
  const sendChatMessage = useCallback(
    (message: string) => {
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        // Queue the chat message for when connection is restored
        enqueueRequest({
          type: "chat",
          payload: { message },
          priority: "normal",
          retryCount: 0,
          maxRetries: 5,
        });

        // Attempt to reconnect
        initializeConnection();
        return;
      }

      const requestId = enqueueRequest({
        type: "chat",
        payload: { message },
        priority: "normal",
        retryCount: 0,
        maxRetries: 3,
      });

      processRequestQueue();
    },
    [socket, enqueueRequest, processRequestQueue, initializeConnection],
  );

  // Graceful disconnect
  const disconnect = useCallback(() => {
    if (heartbeatInterval.current) clearInterval(heartbeatInterval.current);
    if (healthCheckInterval.current)
      clearInterval(healthCheckInterval.current);
    if (connectionTimeout.current) clearTimeout(connectionTimeout.current);

    // Clear retry timeouts
    retryTimeouts.current.forEach((timeout) => clearTimeout(timeout));
    retryTimeouts.current.clear();

    if (socket) {
      socket.close(1000, "Client disconnect");
      setSocket(null);
    }

    // Clear queues
    requestQueue.current = [];
    activeRequests.current.clear();

    updateConnectionState({
      status: "idle",
      context: "Ready to research",
      userFeedbackLevel: "none",
      requestsInFlight: 0,
      queuedRequests: 0,
      backgroundActivity: false,
    });
  }, [socket, updateConnectionState]);

  // Health monitoring
  useEffect(() => {
    if (!socket) return;

    healthCheckInterval.current = window.setInterval(() => {
      const now = Date.now();
      const timeSinceLastActivity = now - lastActivityTime.current;

      // Update uptime
      const uptime =
        connectionStartTime.current > 0
          ? now - connectionStartTime.current
          : 0;

      updateConnectionState({
        uptime,
        backgroundActivity:
          timeSinceLastActivity < finalConfig.heartbeatInterval * 2,
      });

      // Process queued requests
      processRequestQueue();
    }, finalConfig.healthCheckInterval);

    return () => {
      if (healthCheckInterval.current) {
        clearInterval(healthCheckInterval.current);
      }
    };
  }, [socket, finalConfig, updateConnectionState, processRequestQueue]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // Connection state
    socket,
    connectionState,

    // Public methods
    initializeConnection,
    startResearch,
    sendChatMessage,
    disconnect,

    // Utility methods
    getContextualMessage: (status: ConnectionStatus) =>
      getContextualMessage(status, connectionState),

    // Queue information
    getQueueStatus: () => ({
      queued: requestQueue.current.length,
      active: activeRequests.current.size,
      total: requestQueue.current.length + activeRequests.current.size,
    }),

    // Metrics (if enabled)
    getMetrics: finalConfig.enableMetrics
      ? () => ({
        ...metrics.current,
        connectionQuality: connectionState.quality,
        uptime: connectionState.uptime,
      })
      : undefined,
  };
};
