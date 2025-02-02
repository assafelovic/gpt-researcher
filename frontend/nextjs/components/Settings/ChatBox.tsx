import React, { useState, useEffect } from 'react';
import ResearchForm from '../Task/ResearchForm';
import Report from '../Task/Report';
import AgentLogs from '../Task/AgentLogs';
import AccessReport from '../ResearchBlocks/AccessReport';
import { getHost } from '../../helpers/getHost';

interface ChatBoxSettings {
  report_source: string;
  report_type: string;
  tone: string;
}

interface ChatBoxProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
}

interface OutputData {
  pdf?: string;
  docx?: string;
  json?: string;
}

interface WebSocketMessage {
  type: 'logs' | 'report' | 'path';
  output: string | OutputData;
}

export default function ChatBox({ chatBoxSettings, setChatBoxSettings }: ChatBoxProps) {

  const [agentLogs, setAgentLogs] = useState<any[]>([]);
  const [report, setReport] = useState("");
  const [accessData, setAccessData] = useState({});
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const fullHost = getHost()
      const host = fullHost.replace('http://', '').replace('https://', '')
      
      const ws_uri = `${fullHost.includes('https') ? 'wss:' : 'ws:'}//${host}/ws`;
      const newSocket = new WebSocket(ws_uri);
      setSocket(newSocket);

      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data) as WebSocketMessage;
        
        if (data.type === 'logs') {
          setAgentLogs((prevLogs: any[]) => [...prevLogs, data]);
        } else if (data.type === 'report') {
          setReport((prevReport: string) => prevReport + (data.output as string));
        } else if (data.type === 'path') {
          const output = data.output as OutputData;
          setAccessData({
            ...(output.pdf && { pdf: `outputs/${output.pdf}` }),
            ...(output.docx && { docx: `outputs/${output.docx}` }),
            ...(output.json && { json: `outputs/${output.json}` })
          });
        }
      };

      return () => {
        newSocket.close();
      };
    }
  }, []);

  return (
    <div>
      <main className="container" id="form">
        <ResearchForm 
          chatBoxSettings={chatBoxSettings} 
          setChatBoxSettings={setChatBoxSettings}
        />

        {agentLogs?.length > 0 ? <AgentLogs agentLogs={agentLogs} /> : ''}
        <div className="margin-div">
          {report ? <Report report={report} /> : ''}
          {Object.keys(accessData).length > 0 && 
            <AccessReport 
              accessData={accessData} 
              chatBoxSettings={chatBoxSettings} 
              report={report}
            />
          }
        </div>
      </main>
    </div>
  );
}