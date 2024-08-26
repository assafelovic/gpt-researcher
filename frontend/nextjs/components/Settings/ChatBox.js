import React, { useState, useEffect } from 'react';
import ResearchForm from '../Task/ResearchForm';
import Report from '../Task/Report';
import AgentLogs from '../Task/AgentLogs';
import AccessReport from '../Task/AccessReport';

export default function ChatBox({ chatBoxSettings, setChatBoxSettings }) {

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
          {/* {Object.keys(accessData).length != 0 ? <AccessReport accessData={accessData} report={report} /> : ''} */}
        </div>
      </main>
    </div>
  );
}