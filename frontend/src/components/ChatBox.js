import React, { useState } from 'react';
import {addAgentResponse, writeReport, updateDownloadLink, 
  updateScroll, copyToClipboard} from '../helpers/scripts';

export function ChatBox() {
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

  return (
    <div>
      
    </div>
  );
}