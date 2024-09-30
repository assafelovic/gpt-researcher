// Search.js
import React, { useState, useEffect } from 'react';
import ResearchForm from './Task/ResearchForm';
import Report from './Task/Report';
import AgentLogs from './Task/AgentLogs';
import AccessReport from './Task/AccessReport';
import InputArea from './InputArea';

const Search = () => {
  const [task, setTask] = useState<string>('');
  const [reportType, setReportType] = useState<string>('');
  const [reportSource, setReportSource] = useState<string>('');
  const [agentLogs, setAgentLogs] = useState<string[]>([]);
  const [report, setReport] = useState<string>('');
  const [accessData, setAccessData] = useState<string>('');
  const [socket, setSocket] = useState<WebSocket | null>(null);

  const [chatBoxSettings, setChatBoxSettings] = useState({
    report_type: 'multi_agents',
    report_source: 'web',
    tone: 'Objective',
  });

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

  const handleFormSubmit = (
    task: string,
    reportType: string,
    reportSource: string
  ) => {
    setTask(task);
    setReportType(reportType);
    setReportSource(reportSource);

    // Prepare the data to send
    const data = 'start ' + JSON.stringify({
      task: task,
      report_type: reportType,
      report_source: reportSource,
    });

    // Send data to WebSocket server if connected
    if (socket) {
      socket.send(data);
    } else {
      console.error('WebSocket connection is not established.');
    }
  };

  return (
    <div>
      <ResearchForm
        chatBoxSettings={chatBoxSettings}
        setChatBoxSettings={setChatBoxSettings}
      />
      <AgentLogs agentLogs={agentLogs} />
      <Report report={report} />
      <AccessReport accessData={accessData} report={report} />
    </div>
  );
};

export default Search;