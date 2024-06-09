import React, { useState, useEffect } from 'react';
import ResearchForm from './ResearchForm';
import Report from './Report';
import AgentLogs from './AgentLogs';
import AccessReport from './AccessReport';

export default function ChatBox() {
  const [agentLogs, setAgentLogs] = useState([]);
  const [report, setReport] = useState("");
  const [accessData, setAccessData] = useState({});
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
        if (data.type === 'logs') {
          setAgentLogs((prevLogs) => [...prevLogs, data]);
        } else if (data.type === 'report') {
          setReport((prevReport) => prevReport + data.output);
        } else if (data.type === 'path') {
          setAccessData(data);
        }
      };

      return () => {
        newSocket.close();
      };
    }
  }, []);

  const onFormSubmit = (e) => {
    e.preventDefault();
    let { task, report_type, report_source } = e.target;
    setAgentLogs([{ output: "🤔 Thinking about research questions for the task..." }]);
    startResearch(task, report_type, report_source);
  };

  const startResearch = (task, report_type, report_source) => {
    setReport("");
    let data = "start " + JSON.stringify({ task: task.value, report_type: report_type.value, report_source: report_source.value });
    socket.send(data);
  };

  return (
    <div>
      <main className="container" id="form">
        <ResearchForm onFormSubmit={onFormSubmit} defaultReportType="multi_agents" />

        {agentLogs?.length > 0 ? <AgentLogs agentLogs={agentLogs} /> : ''}
        <div className="margin-div">
          {report ? <Report report={report} /> : ''}
          {/* {Object.keys(accessData).length != 0 ? <AccessReport accessData={accessData} report={report} /> : ''} */}
        </div>
      </main>
    </div>
  );
}