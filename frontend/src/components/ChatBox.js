import React, { useState } from 'react';
import ResearchForm from './ResearchForm'
import Report from './Report'

import {addAgentResponse, writeReport, updateDownloadLink, 
  updateScroll, copyToClipboard} from '../helpers/scripts';

export default function ChatBox() {
  const [report, writeReport] = useState("");

  const startResearch = () => {
      // Clear output and reportContainer divs

      document.getElementById("output").innerHTML = "";
      document.getElementById("reportContainer").innerHTML = "";

      addAgentResponse({output: "🤔 Thinking about research questions for the task..."});

      listenToSockEvents();
  }

  const listenToSockEvents = () => {
      const {protocol, host, pathname} = window.location;
      const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${host}${pathname}ws`;
      const socket = new WebSocket(ws_uri);

      socket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'logs') {
              addAgentResponse(data);
          } else if (data.type === 'report') {
              writeReport(data);
          } else if (data.type === 'path') {
              updateDownloadLink(data);
          }
      };

      socket.onopen = (event) => {
          let task = document.querySelector('input[name="task"]').value;
          let report_type = document.querySelector('select[name="report_type"]').value;
          let agent = document.querySelector('input[name="agent"]:checked').value;  // Corrected line
          let data = "start " + JSON.stringify({task: task, report_type: report_type, agent: agent});
          socket.send(data);
      };
  }

  const onSubmittingResearchForm = (arg) => { 
    console.log('accessing child state from parent callback (Research form data logged in ChatBox.js): ', arg) 
  }

  return (
    <div>
      <section className="landing">
          <div className="max-w-5xl mx-auto text-center">
              <h1 className="text-4xl font-extrabold mx-auto lg:text-7xl">
                  Say Goodbye to
                  <span className="sayGoodbye">Hours
                      of Research</span>
              </h1>
              <p className="max-w-5xl mx-auto text-gray-600 mt-8" style="font-size:20px">
                  Say Hello to GPT Researcher, your AI mate for rapid insights and comprehensive research. GPT Researcher
                  takes care of everything from accurate source gathering to organization of research results - all in one
                  platform designed to make your research process a breeze.
              </p>
              <a href="#form" className="btn btn-primary">Get Started</a>
          </div>
      </section>

      <main className="container" id="form">
          <ResearchForm onSubmit={onSubmittingResearchForm}/>

          <div className="margin-div">
              <h2>Agent Output</h2>
              <div id="output"></div>
          </div>
          <Report />
      </main>
    </div>
  );
}