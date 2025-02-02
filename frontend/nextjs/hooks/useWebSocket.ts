import { useRef, useState } from 'react';
import { Data, ChatBoxSettings, QuestionData } from '../types/data';
import { getHost } from '../helpers/getHost';

export const useWebSocket = (setOrderedData: React.Dispatch<React.SetStateAction<Data[]>>, setAnswer: React.Dispatch<React.SetStateAction<string>>, setLoading: React.Dispatch<React.SetStateAction<boolean>>, setShowHumanFeedback: React.Dispatch<React.SetStateAction<boolean>>, setQuestionForHuman: React.Dispatch<React.SetStateAction<boolean | true>>) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const heartbeatInterval = useRef<number>();

  const initializeWebSocket = (promptValue: string, chatBoxSettings: ChatBoxSettings) => {
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

    if (!socket && typeof window !== 'undefined') {
      const fullHost = getHost()
      const host = fullHost.replace('http://', '').replace('https://', '')

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
            setAnswer((prev: any) => prev + data.output);
          } else if (data.type === 'path' || data.type === 'chat') {
            setLoading(false);
          }
        }
      };

      newSocket.onopen = () => {
        const { report_type, report_source, tone } = chatBoxSettings;
        let data = "start " + JSON.stringify({ task: promptValue, report_type, report_source, tone, headers });
        newSocket.send(data);

        heartbeatInterval.current = window.setInterval(() => {
          socket?.send('ping');
        }, 3000); // Send ping every 3 seconds
      };

      newSocket.onclose = () => {
        if (heartbeatInterval.current) {
          clearInterval(heartbeatInterval.current);
        }
        setSocket(null);
      };
    } else if (socket) {
      const { report_type, report_source, tone } = chatBoxSettings;
      let data = "start " + JSON.stringify({ task: promptValue, report_type, report_source, tone, headers });
      socket.send(data);
    }
  };

  return { socket, setSocket, initializeWebSocket };
};