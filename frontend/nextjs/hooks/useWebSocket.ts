import { useState, useEffect, useCallback } from 'react';
import { createWebSocket, sendWebSocketMessage } from '../services/websocket';
import { Data, ChatBoxSettings } from '../types/data';

export const useWebSocket = (onDataReceived: (data: Data) => void) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  const connect = useCallback((onHumanFeedback?: (output: any) => void) => {
    const newSocket = createWebSocket({
      onMessage: onDataReceived,
      onHumanFeedback,
      onOpen: () => setIsConnected(true),
    });
    setSocket(newSocket);
    return newSocket;
  }, [onDataReceived]);

  const startResearch = useCallback((prompt: string, settings: ChatBoxSettings) => {
    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};
    
    const headers = {
      'retriever': apiVariables.RETRIEVER,
      'langchain_api_key': apiVariables.LANGCHAIN_API_KEY,
      'openai_api_key': apiVariables.OPENAI_API_KEY,
      'tavily_api_key': apiVariables.TAVILY_API_KEY,
      'google_api_key': apiVariables.GOOGLE_API_KEY,
      'google_cx_key': apiVariables.GOOGLE_CX_KEY,
      'bing_api_key': apiVariables.BING_API_KEY,
      'searchapi_api_key': apiVariables.SEARCHAPI_API_KEY,
      'serpapi_api_key': apiVariables.SERPAPI_API_KEY,
      'serper_api_key': apiVariables.SERPER_API_KEY,
      'searx_url': apiVariables.SEARX_URL
    };

    const { report_type, report_source, tone } = settings;
    const message = "start " + JSON.stringify({ 
      task: prompt, 
      report_type, 
      report_source, 
      tone, 
      headers 
    });

    sendWebSocketMessage(socket, message);
  }, [socket]);

  const sendChat = useCallback((message: string) => {
    const data = `chat${JSON.stringify({ message })}`;
    sendWebSocketMessage(socket, data);
  }, [socket]);

  const sendFeedback = useCallback((feedback: string | null) => {
    sendWebSocketMessage(socket, JSON.stringify({ 
      type: 'human_feedback', 
      content: feedback 
    }));
  }, [socket]);

  return {
    socket,
    isConnected,
    connect,
    startResearch,
    sendChat,
    sendFeedback
  };
}; 