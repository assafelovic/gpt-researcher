import React, { useState, useRef } from 'react';
import ResearchForm from './ResearchForm'
import Report from './Report'
import AgentLogs from './AgentLogs'
import AccessReport from './AccessReport'

import {addAgentResponse, writeReport, updateDownloadLink} from '../helpers/scripts';

export default function ChatBox() {

  const [task, setTask] = useState("");
  const [report_type, setReportType] = useState("");
  const [agent, setAgent] = useState("");
  const [agentLogs, setAgentLogs] = useState([]);
  const [report, setReport] = useState("");

  const onFormSubmit = (e) => {
    e.preventDefault();
    console.log('form submitted in ChatBox.js: ')
    let {task, agent, report_type} = e.target;

    console.log(task.value, agent.value, report_type.value)
    setTask(task.value)
    setAgent(agent.value)
    setReportType(report_type)
    setAgentLogs([{output: "🤔 Thinking about research questions for the task..."}]);
    startResearch()
  }

  const startResearch = () => {
      // Clear output and reportContainer divs

    //   document.getElementById("output").innerHTML = "";
    //   document.getElementById("reportContainer").innerHTML = "";

      listenToSockEvents();
  }

  const listenToSockEvents = () => {
      const {protocol, host, pathname} = window.location;
      const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${host}${pathname}ws`;
      const socket = new WebSocket(ws_uri);

      socket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'logs') {
            setAgentLogs([...agentLogs, ...data])
          } else if (data.type === 'report') {
              writeReport(data);
          } else if (data.type === 'path') {
              updateDownloadLink(data);
          }
      };

      socket.onopen = (event) => {
        //   let task = document.querySelector('input[name="task"]').value;
        //   let report_type = document.querySelector('select[name="report_type"]').value;
        //   let agent = document.querySelector('input[name="agent"]:checked').value;  // Corrected line
          let data = "start " + JSON.stringify({task: task, report_type: report_type, agent: agent});
          socket.send(data);
      };
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
          {report ? 
              <div className="margin-div">
                  <Report report={report}/>
                  <AccessReport />
            </div>
           
          : ''}
          
      </main>
    </div>
  );
}