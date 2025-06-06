import { useRef, useState, useEffect, useCallback } from 'react';
import { Data, ChatBoxSettings, QuestionData } from '../types/data';
import { getHost } from '../helpers/getHost';

export const useWebSocket = (
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>, 
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>,
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>,
) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const heartbeatInterval = useRef<number>();

  // Cleanup function for heartbeat
  useEffect(() => {
    return () => {
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
      }
    };
  }, []);

  const startHeartbeat = (ws: WebSocket) => {
    // Clear any existing heartbeat
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
    }
    
    // Start new heartbeat
    heartbeatInterval.current = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000); // Send ping every 30 seconds
  };

  const initializeWebSocket = useCallback((promptValue: string, chatBoxSettings: ChatBoxSettings) => {
    console.log('🔌 WebSocket initialization called with:', { promptValue, chatBoxSettings });
    
    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};

    if (!socket && typeof window !== 'undefined') {
      
      let fullHost = getHost()
      const protocol = fullHost.includes('https') ? 'wss:' : 'ws:'
      const cleanHost = fullHost.replace('http://', '').replace('https://', '')
      const ws_uri = `${protocol}//${cleanHost}/ws`

      console.log('🌐 Connecting to WebSocket:', ws_uri);

      const newSocket = new WebSocket(ws_uri);
      setSocket(newSocket);

      newSocket.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        console.log('📋 Sending research request with chatBoxSettings:', chatBoxSettings);
        
        const domainFilters = JSON.parse(localStorage.getItem('domainFilters') || '[]');
        const domains = domainFilters ? domainFilters.map((domain: any) => domain.value) : [];
        const { report_type, report_source, tone, mcp_enabled, mcp_configs } = chatBoxSettings;
        
        const requestData: any = { 
          task: promptValue,
          report_type, 
          report_source, 
          tone,
          query_domains: domains
        };

        // Add MCP configuration if enabled
        if (mcp_enabled && mcp_configs && mcp_configs.length > 0) {
          requestData.mcp_enabled = true;
          requestData.mcp_strategy = "fast"; // Always use fast strategy as default
          requestData.mcp_configs = mcp_configs;
          console.log('🔧 Including MCP configuration:', { mcp_enabled, mcp_configs });
        }
        
        let data = "start " + JSON.stringify(requestData);
        
        console.log('📤 Sending WebSocket message:', data);
        newSocket.send(data);
        startHeartbeat(newSocket);
      };

      newSocket.onmessage = (event) => {
        console.log('📥 WebSocket message received:', event.data);
        
        try {
          // Handle ping response
          if (event.data === 'pong') {
            console.log('🏓 Received pong response');
            return;
          }

          // Try to parse JSON data
          const data = JSON.parse(event.data);
          console.log('📊 Parsed WebSocket data:', data);
          
          if (data.type === 'human_feedback' && data.content === 'request') {
            console.log('👤 Human feedback requested');
            setQuestionForHuman(data.output);
            setShowHumanFeedback(true);
          } else {
            const contentAndType = `${data.content}-${data.type}`;
            setOrderedData((prevOrder) => [...prevOrder, { ...data, contentAndType }]);

            if (data.type === 'report') {
              console.log('📄 Received report data, updating answer');
              setAnswer((prev: string) => prev + data.output);
            } else if (data.type === 'path' || data.type === 'chat') {
              console.log('🏁 Research completed, stopping loading');
              setLoading(false);
            }
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error, 'Raw data:', event.data);
        }
      };

      newSocket.onclose = () => {
        console.log('🔌 WebSocket connection closed');
        if (heartbeatInterval.current) {
          clearInterval(heartbeatInterval.current);
        }
        setSocket(null);
      };

      newSocket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        if (heartbeatInterval.current) {
          clearInterval(heartbeatInterval.current);
        }
      };
    } else if (socket) {
      console.log('⚠️ WebSocket already exists, skipping initialization');
    }
  }, [socket]); // Remove currentApiUrl from dependencies

  return { socket, setSocket, initializeWebSocket };
};