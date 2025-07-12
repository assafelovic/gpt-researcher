import React, { createContext, useContext, useEffect, useCallback, useMemo } from 'react';
import { Data, ChatBoxSettings } from '../types/data';
import { useResilientConnection, ResilientConnectionState, ConnectionStatus } from './useResilientConnection';

interface ResilientConnectionContextType {
  // Connection state
  connectionState: ResilientConnectionState;
  isConnected: boolean;
  isConnecting: boolean;
  isProcessing: boolean;
  hasError: boolean;

  // Actions
  startResearch: (promptValue: string, chatBoxSettings: ChatBoxSettings) => void;
  sendChatMessage: (message: string) => void;
  reconnect: () => void;
  disconnect: () => void;

  // Status helpers
  getStatusMessage: () => string;
  getConnectionQuality: () => "excellent" | "good" | "fair" | "poor" | "critical";
  shouldShowStatus: () => boolean;

  // Metrics (optional)
  getMetrics?: () => any;
  getQueueStatus: () => { queued: number; active: number; total: number };

  // Configuration
  updateConfig: (config: Partial<any>) => void;
}

const ResilientConnectionContext = createContext<ResilientConnectionContextType | undefined>(undefined);

interface ResilientConnectionProviderProps {
  children: React.ReactNode;
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>;
  setAnswer: React.Dispatch<React.SetStateAction<string>>;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>;
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>;
  config?: {
    // Retry configuration
    maxRetries?: number;
    baseRetryDelay?: number;
    maxRetryDelay?: number;
    retryBackoffFactor?: number;
    jitterRange?: number;

    // Connection settings
    connectionTimeout?: number;
    heartbeatInterval?: number;
    healthCheckInterval?: number;

    // User experience
    silentRetryThreshold?: number;
    contextualFeedbackDelay?: number;

    // Security
    sanitizeErrors?: boolean;
    logLevel?: "none" | "errors" | "warnings" | "info" | "debug";
    enableMetrics?: boolean;
  };
}

export const ResilientConnectionProvider: React.FC<ResilientConnectionProviderProps> = ({
  children,
  setOrderedData,
  setAnswer,
  setLoading,
  setShowHumanFeedback,
  setQuestionForHuman,
  config = {}
}) => {
  // Initialize the resilient connection hook
  const {
    socket,
    connectionState,
    initializeConnection,
    startResearch,
    sendChatMessage,
    disconnect,
    getContextualMessage,
    getQueueStatus,
    getMetrics
  } = useResilientConnection(
    setOrderedData,
    setAnswer,
    setLoading,
    setShowHumanFeedback,
    setQuestionForHuman,
    config
  );

  // Derived state for easier consumption
  const isConnected = useMemo(() =>
    connectionState.status === 'connected' ||
    connectionState.status === 'ready' ||
    connectionState.status === 'processing' ||
    connectionState.status === 'streaming'
    , [connectionState.status]);

  const isConnecting = useMemo(() =>
    connectionState.status === 'initializing' ||
    connectionState.status === 'connecting' ||
    connectionState.status === 'reconnecting'
    , [connectionState.status]);

  const isProcessing = useMemo(() =>
    connectionState.status === 'processing' ||
    connectionState.status === 'streaming'
    , [connectionState.status]);

  const hasError = useMemo(() =>
    connectionState.status === 'failed' ||
    connectionState.status === 'suspended'
    , [connectionState.status]);

  // Auto-connect on mount
  useEffect(() => {
    if (connectionState.status === 'idle' && !socket) {
      initializeConnection();
    }
  }, [connectionState.status, socket, initializeConnection]);

  // Auto-reconnect on visibility change (when user returns to tab)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && connectionState.status === 'failed') {
        console.log('Tab became visible, attempting to reconnect...');
        initializeConnection();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [connectionState.status, initializeConnection]);

  // Auto-reconnect on network status change
  useEffect(() => {
    const handleOnline = () => {
      if (connectionState.status === 'failed' || !socket) {
        console.log('Network came back online, attempting to reconnect...');
        initializeConnection();
      }
    };

    const handleOffline = () => {
      console.log('Network went offline');
      // The connection will handle this gracefully through its own error handling
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [connectionState.status, socket, initializeConnection]);

  // Smart retry logic based on user activity
  useEffect(() => {
    let retryTimeout: number;

    // Only retry if there's an error and the user might be waiting
    if (hasError && connectionState.retryCount < (config.maxRetries || 15)) {
      const delay = Math.min(
        (config.baseRetryDelay || 1000) * Math.pow(1.5, connectionState.retryCount),
        config.maxRetryDelay || 30000
      );

      retryTimeout = window.setTimeout(() => {
        console.log(`Auto-retry attempt ${connectionState.retryCount + 1}`);
        initializeConnection();
      }, delay);
    }

    return () => {
      if (retryTimeout) {
        clearTimeout(retryTimeout);
      }
    };
  }, [hasError, connectionState.retryCount, config, initializeConnection]);

  // Helper functions
  const getStatusMessage = useCallback((): string => {
    return getContextualMessage(connectionState.status);
  }, [getContextualMessage, connectionState.status]);

  const getConnectionQuality = useCallback(() => {
    return connectionState.quality.level;
  }, [connectionState.quality.level]);

  const shouldShowStatus = useCallback((): boolean => {
    // Show status based on user feedback level
    switch (connectionState.userFeedbackLevel) {
      case 'none':
        return false;
      case 'minimal':
        return connectionState.status === 'reconnecting' ||
          connectionState.status === 'failed' ||
          (connectionState.isRetrying && connectionState.retryCount > 2);
      case 'contextual':
        return connectionState.status !== 'idle' &&
          connectionState.status !== 'ready' &&
          connectionState.status !== 'connected';
      case 'detailed':
        return true;
      default:
        return false;
    }
  }, [connectionState]);

  const reconnect = useCallback(() => {
    console.log('Manual reconnection requested');
    initializeConnection();
  }, [initializeConnection]);

  const updateConfig = useCallback((newConfig: Partial<any>) => {
    // This would typically update the configuration
    // For now, we log it as the hook doesn't support dynamic config updates
    console.log('Config update requested:', newConfig);
    // In a full implementation, you'd want to restart the connection with new config
  }, []);

  // Create context value
  const contextValue: ResilientConnectionContextType = useMemo(() => ({
    // Connection state
    connectionState,
    isConnected,
    isConnecting,
    isProcessing,
    hasError,

    // Actions
    startResearch,
    sendChatMessage,
    reconnect,
    disconnect,

    // Status helpers
    getStatusMessage,
    getConnectionQuality,
    shouldShowStatus,

    // Metrics
    getMetrics,
    getQueueStatus,

    // Configuration
    updateConfig,
  }), [
    connectionState,
    isConnected,
    isConnecting,
    isProcessing,
    hasError,
    startResearch,
    sendChatMessage,
    reconnect,
    disconnect,
    getStatusMessage,
    getConnectionQuality,
    shouldShowStatus,
    getMetrics,
    getQueueStatus,
    updateConfig
  ]);

  return (
    <ResilientConnectionContext.Provider value={contextValue}>
      {children}
    </ResilientConnectionContext.Provider>
  );
};

// Custom hook to use the context
export const useResilientConnectionContext = (): ResilientConnectionContextType => {
  const context = useContext(ResilientConnectionContext);
  if (context === undefined) {
    throw new Error("useResilientConnectionContext must be used within a ResilientConnectionProvider");
  }
  return context;
};

// Hook for simple connection status
export const useConnectionStatus = () => {
  const { connectionState, isConnected, isConnecting, hasError, getStatusMessage } = useResilientConnectionContext();

  return {
    status: connectionState.status,
    isConnected,
    isConnecting,
    hasError,
    message: getStatusMessage(),
    quality: connectionState.quality.level,
    uptime: connectionState.uptime,
    retryCount: connectionState.retryCount,
  };
};

// Hook for research operations
export const useResearch = () => {
  const { startResearch, isProcessing, connectionState } = useResilientConnectionContext();

  return {
    startResearch,
    isProcessing,
    progress: connectionState.progress,
    currentTask: connectionState.currentTask,
    canStartResearch: connectionState.status === "ready" || connectionState.status === "connected",
  };
};

// Hook for chat operations
export const useChat = () => {
  const { sendChatMessage, connectionState } = useResilientConnectionContext();

  return {
    sendChatMessage,
    canChat: connectionState.status === "ready",
  };
};

// Hook for connection metrics (optional)
export const useConnectionMetrics = () => {
  const { getMetrics, getQueueStatus, connectionState } = useResilientConnectionContext();

  return {
    getMetrics: getMetrics || (() => null),
    queueStatus: getQueueStatus(),
    quality: connectionState.quality,
    uptime: connectionState.uptime,
    backgroundActivity: connectionState.backgroundActivity,
  };
};

// HOC for components that need connection status
export const withConnectionStatus = <P extends object>(
  WrappedComponent: React.ComponentType<P & { connectionStatus: ReturnType<typeof useConnectionStatus> }>
) => {
  const WithConnectionStatusComponent = (props: P) => {
    const connectionStatus = useConnectionStatus();

    return <WrappedComponent {...props} connectionStatus={connectionStatus} />;
  };

  WithConnectionStatusComponent.displayName = `withConnectionStatus(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithConnectionStatusComponent;
};

export default ResilientConnectionContext;
