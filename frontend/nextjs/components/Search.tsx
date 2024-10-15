import React, { useState, useEffect } from 'react';
import ResearchForm from './Task/ResearchForm';
import Report from './Task/Report';
import AgentLogs from './Task/AgentLogs';
import AccessReport from './Task/AccessReport';

const Search = () => {
  // State for chatBoxSettings
  const [chatBoxSettings, setChatBoxSettings] = useState({
    report_type: '',
    report_source: '',
    tone: '',
  });

  const [task, setTask] = useState<string>('');
  const [agentLogs, setAgentLogs] = useState<any[]>([]);
  const [report, setReport] = useState<string>('');
  const [accessData, setAccessData] = useState<string>('');
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const { protocol, pathname } = window.location;
      let { host } = window.location;
      host = host.includes('localhost') ? 'localhost:8000' : host;
      const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${host}${pathname}ws`;

      const newSocket = new WebSocket(ws_uri);
      setSocket(newSocket);

      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agentLogs') {
          setAgentLogs((prevLogs) => [...prevLogs, data.output]);
        } else if (data.type === 'report') {
          setReport(data.output);
        } else if (data.type === 'accessData') {
          setAccessData(data.output);
        }
      };

      return () => newSocket.close();
    }
  }, []);

  const handleFormSubmit = (task: string, reportType: string, reportSource: string) => {
    setTask(task);

    // Update reportType and reportSource in the settings
    setChatBoxSettings((prev) => ({
      ...prev,
      report_type: reportType,
      report_source: reportSource,
    }));

    // Sending data to WebSocket server
    const data = JSON.stringify({ task, report_type: reportType, report_source: reportSource });
    if (socket) socket.send(`start ${data}`);
  };

  return (
    <div>
      {/* Pass chatBoxSettings and setChatBoxSettings to ResearchForm */}
      <ResearchForm
        onFormSubmit={handleFormSubmit}
        chatBoxSettings={chatBoxSettings}
        setChatBoxSettings={setChatBoxSettings}
      />
      <AgentLogs agentLogs={agentLogs} />
      <Report report={report} />
      <AccessReport accessData={accessData} report={undefined} />
    </div>
  );
};

export default Search;