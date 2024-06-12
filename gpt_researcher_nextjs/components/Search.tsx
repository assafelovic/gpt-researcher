// Search.js
import React, { useState, useEffect } from 'react';
import ResearchForm from './Task/ResearchForm';
import Report from './Task/Report';
import AgentLogs from './Task/AgentLogs';
import AccessReport from './Task/AccessReport';
import InputArea from './InputArea';


const Search = () => {
  const [task, setTask] = useState('');
  const [reportType, setReportType] = useState('');
  const [reportSource, setReportSource] = useState('');
  const [agentLogs, setAgentLogs] = useState([]);
  const [report, setReport] = useState('');
  const [accessData, setAccessData] = useState('');
  const [socket, setSocket] = useState(null);

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

  const handleFormSubmit = (task, reportType, reportSource) => {
    setTask(task);
    setReportType(reportType);
    setReportSource(reportSource);
    // Send data to WebSocket server if needed
    let data = "start " + JSON.stringify({ task: task.value, report_type: report_type.value, report_source: report_source.value });
    socket.send(data);
  };

  return (
    <div>
      
      <ResearchForm onFormSubmit={handleFormSubmit} defaultReportType="multi_agents"/>
      
      <AgentLogs agentLogs={agentLogs} />
      <Report report={report} />
      <AccessReport accessData={accessData} />
    </div>
  );
};

export default Search;