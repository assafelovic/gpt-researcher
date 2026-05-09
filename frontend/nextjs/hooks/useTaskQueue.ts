/**
 * useTaskQueue — Persistent Task Queue Hook
 *
 * Submits research tasks via HTTP POST /api/tasks, then streams logs
 * via WebSocket /ws/tasks/{task_id}.
 *
 * Key properties:
 *   - Disconnecting / refreshing does NOT cancel the task.
 *   - On reconnect, all past logs are replayed from the server.
 *   - Multiple tasks can be queued; only one runs at a time (server-side).
 */

import { useRef, useState, useCallback } from 'react';
import { Data, ChatBoxSettings } from '../types/data';
import { getHost } from '../helpers/getHost';

export type TaskStatus = 'idle' | 'queued' | 'running' | 'done' | 'failed' | 'cancelled';

export interface TaskInfo {
  task_id: string;
  status: TaskStatus;
  queued_at: number;
}

export const useTaskQueue = (
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>,
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>
) => {
  const [taskInfo, setTaskInfo] = useState<TaskInfo | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus>('idle');
  const socketRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<number | undefined>(undefined);

  const stopHeartbeat = () => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = undefined;
    }
  };

  const startHeartbeat = (ws: WebSocket) => {
    stopHeartbeat();
    heartbeatRef.current = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 30_000);
  };

  /** Connect (or reconnect) to the log stream for an existing task_id */
  const connectLogStream = useCallback(
    (task_id: string) => {
      // Close any previous stream
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close(1000, 'Reconnecting');
      }

      const host = getHost();
      const protocol = host.includes('https') ? 'wss:' : 'ws:';
      const cleanHost = host.replace(/^https?:\/\//, '');
      const wsUrl = `${protocol}//${cleanHost}/ws/tasks/${task_id}`;

      console.log(`[TaskQueue] Connecting log stream: ${wsUrl}`);
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log(`[TaskQueue] Log stream connected for ${task_id}`);
        startHeartbeat(ws);
      };

      ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') return;
          const data = JSON.parse(event.data);

          if (data.type === 'ping') return; // server keepalive

          if (data.type === 'task_status') {
            const st = data.status as TaskStatus;
            setTaskStatus(st);
            if (st === 'done' || st === 'failed' || st === 'cancelled') {
              setLoading(false);
              stopHeartbeat();
            }
            return;
          }

          if (data.type === 'error') {
            console.error(`[TaskQueue] Server error: ${data.output}`);
          } else if (data.type === 'human_feedback' && data.content === 'request') {
            setQuestionForHuman(data.output);
            setShowHumanFeedback(true);
          } else {
            const contentAndType = `${data.content}-${data.type}`;
            setOrderedData((prev) => [...prev, { ...data, contentAndType }]);

            if (data.type === 'report') {
              setAnswer((prev) => prev + data.output);
            } else if (data.type === 'report_complete') {
              setAnswer(data.output);
            } else if (data.type === 'path') {
              setLoading(false);
            }
          }
        } catch (err) {
          console.error('[TaskQueue] Failed to parse message:', err, event.data);
        }
      };

      ws.onclose = (event) => {
        console.log(`[TaskQueue] Log stream closed: code=${event.code}`);
        stopHeartbeat();
      };

      ws.onerror = (err) => {
        console.error('[TaskQueue] Log stream error:', err);
        stopHeartbeat();
      };
    },
    [setOrderedData, setAnswer, setLoading, setShowHumanFeedback, setQuestionForHuman]
  );

  /** Submit a new research task to the queue */
  const submitTask = useCallback(
    async (promptValue: string, chatBoxSettings: ChatBoxSettings): Promise<string | null> => {
      const host = getHost();
      const storedConfig = localStorage.getItem('apiVariables');
      const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
      const domainFilters = JSON.parse(localStorage.getItem('domainFilters') || '[]');
      const domains = domainFilters.map((d: any) => d.value);

      const { report_type, report_source, tone, mcp_enabled, mcp_configs, mcp_strategy } =
        chatBoxSettings;

      const params = {
        task: promptValue,
        report_type,
        report_source,
        tone,
        query_domains: domains,
        mcp_enabled: mcp_enabled || false,
        mcp_strategy: mcp_strategy || 'fast',
        mcp_configs: mcp_configs || [],
        headers: apiVariables,
      };

      try {
        console.log('[TaskQueue] Submitting task:', promptValue.slice(0, 60));
        const resp = await fetch(`${host}/api/tasks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
        });

        if (!resp.ok) {
          const errText = await resp.text();
          throw new Error(`HTTP ${resp.status}: ${errText}`);
        }

        const info: TaskInfo = await resp.json();
        console.log('[TaskQueue] Task created:', info.task_id, info.status);
        setTaskInfo(info);
        setTaskStatus(info.status);
        setLoading(true);

        // Immediately connect to the log stream
        connectLogStream(info.task_id);

        return info.task_id;
      } catch (err) {
        console.error('[TaskQueue] Submit failed:', err);
        setLoading(false);
        return null;
      }
    },
    [connectLogStream]
  );

  /** Reconnect log stream for an existing task_id (after page refresh) */
  const reconnect = useCallback(
    (task_id: string) => {
      setLoading(true);
      connectLogStream(task_id);
    },
    [connectLogStream, setLoading]
  );

  return {
    taskInfo,
    taskStatus,
    submitTask,
    reconnect,
  };
};
