import { useEffect, useRef, useState } from 'react';
import { Data } from '@/types/data';
import { getHost } from '../helpers/getHost';

interface UseWebSocketProps {
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>;
  setAnswer: React.Dispatch<React.SetStateAction<string>>;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>;
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean>>;
}

export const useWebSocket = (
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>,
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean>>
) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const heartbeatInterval = useRef<number>();

  const initializeWebSocket = (question: string, settings: any) => {
    if (typeof window !== 'undefined') {
      const fullHost = getHost();
      const host = fullHost.replace('http://', '').replace('https://', '');
      
      const ws_uri = `${fullHost.includes('https') ? 'wss:' : 'ws:'}//${host}/ws`;
      const newSocket = new WebSocket(ws_uri);
      setSocket(newSocket);

      newSocket.onopen = () => {
        newSocket.send(JSON.stringify({ 
          question, 
          settings 
        }));

        // Start heartbeat
        heartbeatInterval.current = window.setInterval(() => {
          if (newSocket.readyState === WebSocket.OPEN) {
            newSocket.send('ping');
          }
        }, 3000);
      };

      newSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'human_feedback') {
            setShowHumanFeedback(true);
            setQuestionForHuman(data.question_for_human || false);
          } else {
            setOrderedData(prevOrder => [...prevOrder, data]);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      newSocket.onclose = () => {
        setLoading(false);
        if (heartbeatInterval.current) {
          clearInterval(heartbeatInterval.current);
        }
      };

      newSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setLoading(false);
      };
    }
  };

  useEffect(() => {
    return () => {
      if (socket) {
        socket.close();
      }
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
      }
    };
  }, [socket]);

  return {
    socket,
    initializeWebSocket
  };
};