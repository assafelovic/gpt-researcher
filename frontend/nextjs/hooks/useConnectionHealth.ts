import { useState, useEffect, useRef, useCallback } from 'react';

export interface ConnectionHealth {
  quality: "excellent" | "good" | "fair" | "poor" | "disconnected";
  latency: number;
  stability: number;
  lastPingTime: number;
  consecutiveFailures: number;
  uptime: number;
}

interface ConnectionHealthConfig {
  pingInterval: number;
  healthCheckInterval: number;
  latencyThresholds: {
    excellent: number;
    good: number;
    fair: number;
  };
  stabilityWindow: number;
}

const DEFAULT_CONFIG: ConnectionHealthConfig = {
  pingInterval: 30000, // 30 seconds
  healthCheckInterval: 5000, // 5 seconds
  latencyThresholds: {
    excellent: 100,
    good: 300,
    fair: 1000,
  },
  stabilityWindow: 10, // Last 10 measurements
};

export const useConnectionHealth = (
  socket: WebSocket | null,
  config: Partial<ConnectionHealthConfig> = {}
) => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  const [health, setHealth] = useState<ConnectionHealth>({
    quality: "disconnected",
    latency: 0,
    stability: 0,
    lastPingTime: 0,
    consecutiveFailures: 0,
    uptime: 0,
  });

  const pingTimes = useRef<number[]>([]);
  const latencyHistory = useRef<number[]>([]);
  const connectionStartTime = useRef<number>(0);
  const healthCheckInterval = useRef<number>();
  const lastPingTime = useRef<number>(0);

  // Calculate connection quality based on latency
  const calculateQuality = useCallback((latency: number, stability: number): ConnectionHealth['quality'] => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return "disconnected";
    }

    if (latency <= finalConfig.latencyThresholds.excellent && stability > 0.8) {
      return "excellent";
    } else if (latency <= finalConfig.latencyThresholds.good && stability > 0.6) {
      return "good";
    } else if (latency <= finalConfig.latencyThresholds.fair && stability > 0.4) {
      return "fair";
    } else {
      return "poor";
    }
  }, [socket, finalConfig.latencyThresholds]);

  // Calculate stability based on latency consistency
  const calculateStability = useCallback((latencies: number[]): number => {
    if (latencies.length < 2) return 1;

    const mean = latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length;
    const variance = latencies.reduce((sum, lat) => sum + Math.pow(lat - mean, 2), 0) / latencies.length;
    const standardDeviation = Math.sqrt(variance);

    // Normalize stability (lower deviation = higher stability)
    const maxAcceptableDeviation = 200; // ms
    const stability = Math.max(0, 1 - (standardDeviation / maxAcceptableDeviation));

    return Math.min(1, stability);
  }, []);

  // Send ping and measure latency
  const sendPing = useCallback(() => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    const pingTime = Date.now();
    lastPingTime.current = pingTime;
    pingTimes.current.push(pingTime);

    // Clean up old ping times (keep only recent ones)
    const cutoff = pingTime - (finalConfig.stabilityWindow * finalConfig.pingInterval);
    pingTimes.current = pingTimes.current.filter(time => time > cutoff);

    socket.send("ping");
  }, [socket, finalConfig.pingInterval, finalConfig.stabilityWindow]);

  // Handle pong response
  const handlePong = useCallback(() => {
    const now = Date.now();
    const latency = now - lastPingTime.current;

    if (latency > 0) {
      latencyHistory.current.push(latency);

      // Keep only recent latency measurements
      if (latencyHistory.current.length > finalConfig.stabilityWindow) {
        latencyHistory.current = latencyHistory.current.slice(-finalConfig.stabilityWindow);
      }

      const avgLatency = latencyHistory.current.reduce((sum, lat) => sum + lat, 0) / latencyHistory.current.length;
      const stability = calculateStability(latencyHistory.current);
      const quality = calculateQuality(avgLatency, stability);
      const uptime = connectionStartTime.current > 0 ? now - connectionStartTime.current : 0;

      setHealth(prev => ({
        ...prev,
        quality,
        latency: Math.round(avgLatency),
        stability: Math.round(stability * 100) / 100,
        lastPingTime: now,
        consecutiveFailures: 0,
        uptime,
      }));
    }
  }, [calculateQuality, calculateStability, finalConfig.stabilityWindow]);

  // Handle connection failure
  const handleConnectionFailure = useCallback(() => {
    setHealth(prev => ({
      ...prev,
      quality: "disconnected",
      consecutiveFailures: prev.consecutiveFailures + 1,
    }));
  }, []);

  // Monitor connection health
  useEffect(() => {
    if (!socket) {
      setHealth(prev => ({
        ...prev,
        quality: "disconnected",
        latency: 0,
        stability: 0,
        uptime: 0,
      }));
      return;
    }

    // Reset health when socket changes
    if (socket.readyState === WebSocket.OPEN) {
      connectionStartTime.current = Date.now();
      latencyHistory.current = [];
      pingTimes.current = [];

      setHealth(prev => ({
        ...prev,
        quality: "good", // Start optimistic
        consecutiveFailures: 0,
      }));
    }

    // Set up health monitoring
    healthCheckInterval.current = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        sendPing();
      } else {
        handleConnectionFailure();
      }
    }, finalConfig.healthCheckInterval);

    return () => {
      if (healthCheckInterval.current) {
        clearInterval(healthCheckInterval.current);
      }
    };
  }, [socket, sendPing, handleConnectionFailure, finalConfig.healthCheckInterval]);

  // Listen for pong messages
  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event: MessageEvent) => {
      if (event.data === "pong") {
        handlePong();
      }
    };

    socket.addEventListener("message", handleMessage);

    return () => {
      socket.removeEventListener("message", handleMessage);
    };
  }, [socket, handlePong]);

  // Get health status description
  const getHealthDescription = useCallback((quality: ConnectionHealth['quality']): string => {
    switch (quality) {
      case "excellent":
        return "Excellent connection";
      case "good":
        return "Good connection";
      case "fair":
        return "Fair connection";
      case "poor":
        return "Poor connection";
      case "disconnected":
        return "Disconnected";
      default:
        return "Unknown";
    }
  }, []);

  // Get health color for UI
  const getHealthColor = useCallback((quality: ConnectionHealth['quality']): string => {
    switch (quality) {
      case "excellent":
        return "text-green-400";
      case "good":
        return "text-green-300";
      case "fair":
        return "text-yellow-400";
      case "poor":
        return "text-orange-400";
      case "disconnected":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  }, []);

  return {
    health,
    getHealthDescription,
    getHealthColor,
    sendPing,
  };
};
