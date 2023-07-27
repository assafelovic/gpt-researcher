import React, { useState, useEffect } from 'react';
import ResearchForm from './ResearchForm'
import Report from './Report'
import AgentLogs from './AgentLogs'
import AccessReport from './AccessReport'

const {protocol, pathname} = window.location;
let {host} = window.location;
host = host.includes('localhost') ? 'localhost:8000' : host;
const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${host}${pathname}ws`;
const socket = new WebSocket(ws_uri);

export default function ChatBox() {

  const [agentLogs, setAgentLogs] = useState([]);
  const [report, setReport] = useState("");
  const [accessData, setAccessData] = useState({});
  
  useEffect(() => {
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'logs') {
            setAgentLogs([...agentLogs, data])
        } else if (data.type === 'report') {
            setReport(report+data.output);
        } else if (data.type === 'path') {
            setAccessData(data);
        }
    };
  }, [agentLogs, report, accessData])

  const onFormSubmit = (e) => {
    e.preventDefault();
    let {task, agent, report_type} = e.target;
    setAgentLogs([{output: "🤔 Thinking about research questions for the task..."}]);
    startResearch(task, report_type, agent)
  }

  const startResearch = (task, report_type, agent) => {     
      setReport("")
      let data = "start " + JSON.stringify({task: task.value, report_type: report_type.value, agent: agent.value});
      socket.send(data);
  }

  return (
    <div>
      <section className="landing">
          <div className="max-w-5xl mx-auto text-center">
              <h1 className="text-4xl font-extrabold mx-auto lg:text-7xl">
                  Say Hello to
                  <span className="sayGoodbye"> GPTBud</span>
              </h1>
              <p className="max-w-5xl mx-auto text-gray-600 mt-8" style={{fontSize: "20px"}}>
                  The power of Google Search & GPT Combined for a Better Search Experience.
              </p>
              <a href="#form" className="btn btn-primary">Get Started</a>
          </div>
      </section>

      <main className="container" id="form">
          <ResearchForm onFormSubmit={onFormSubmit}/>

          {agentLogs?.length > 0 ? <AgentLogs agentLogs={agentLogs}/> : ''}
          <div className="margin-div">
            {report ? <Report report={report}/> : ''}
            {Object.keys(accessData).length != 0 ? <AccessReport accessData={accessData} report={report} /> : ''}               
          </div>
          
      </main>
    </div>
  );
}