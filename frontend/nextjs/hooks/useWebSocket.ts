import { useRef, useState } from 'react';
import { Data, ChatBoxSettings, QuestionData } from '../types/data';
import { getHost } from '../helpers/getHost';

export const useWebSocket = (
  setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>,
  setAnswer: React.Dispatch<React.SetStateAction<string>>, 
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>,
  setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>
) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const heartbeatInterval = useRef<number>();

  const initializeWebSocket = (promptValue: string, chatBoxSettings: ChatBoxSettings) => {
    const storedConfig = localStorage.getItem('apiVariables');
    const apiVariables = storedConfig ? JSON.parse(storedConfig) : {};

    if (!socket && typeof window !== 'undefined') {
      const fullHost = getHost();
      const host = fullHost.replace('http://', '').replace('https://', '');
      
      const ws_uri = `${fullHost.includes('https') ? 'wss:' : 'ws:'}//${host}/ws`;

      const newSocket = new WebSocket(ws_uri);
      setSocket(newSocket);

      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'human_feedback' && data.content === 'request') {
          setQuestionForHuman(data.output);
          setShowHumanFeedback(true);
        } else {
          const contentAndType = `${data.content}-${data.type}`;
          setOrderedData((prevOrder) => [...prevOrder, { ...data, contentAndType }]);

          if (data.type === 'report') {
            setAnswer((prev: string) => prev + data.output);
          } else if (data.type === 'path' || data.type === 'chat') {
            setLoading(false);
          }
        }
      };

      newSocket.onopen = () => {
        const { report_type, report_source, tone, query_domains } = chatBoxSettings;
        let data = "start " + JSON.stringify({ 
          task: promptValue,
          report_type, 
          report_source, 
          tone,
          query_domains
        });
        newSocket.send(data);

        heartbeatInterval.current = window.setInterval(() => {
          if (newSocket.readyState === WebSocket.OPEN) {
            newSocket.send('ping');
          }
        }, 3000);
      };

      newSocket.onclose = () => {
        if (heartbeatInterval.current) {
          clearInterval(heartbeatInterval.current);
        }
        setSocket(null);
      };
    } else if (socket) {
      const { report_type, report_source, tone } = chatBoxSettings;
      let data = "start " + JSON.stringify({ 
        task: promptValue, 
        report_type, 
        report_source, 
        tone 
      });
      socket.send(data);
    }
  };

  return { socket, setSocket, initializeWebSocket };
};